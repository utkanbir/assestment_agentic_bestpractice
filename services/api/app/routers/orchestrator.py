# S4-AA-001..008: Orchestrator read-only endpoints (frontend için)
# Orchestrator'ın ürettiği sonuçlar PostgreSQL'deki reports tablosundan ve
# SPARQL endpoint'inden okunur — orchestrator bu endpoint'lere yazmaz, sadece okur.
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Finding, Recommendation, Report, Risk
from app.services import sparql_client

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class RiskHeatmapCell(BaseModel):
    capability_area: str
    severity: str
    risk_count: int
    workstreams: list[str]
    max_confidence: float


class ExecutiveSummaryOut(BaseModel):
    assessment_id: str
    summary: str
    generated_at: str
    total_risks: int
    critical_count: int
    dependency_count: int
    conflict_count: int


class RoadmapItemOut(BaseModel):
    id: str | None = None
    title: str
    description: str
    horizon: str
    priority: int
    workstreams: list[str]
    effort: str
    addresses_conflict: bool = False
    consolidated: bool = False


class DependencyOut(BaseModel):
    workstream_a: str
    workstream_b: str
    dependency_type: str
    shared_capability_area: str | None = None
    conflict_signal: str | None = None


@router.get("/{assessment_id}/risk-heatmap", response_model=list[RiskHeatmapCell])
async def get_risk_heatmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[RiskHeatmapCell]:
    """DB-based risk heatmap: findings grouped by severity + workstream (S9-BA-003)."""
    try:
        from app.models.assessment import Task

        # Fetch tasks for assessment
        task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
        tasks = task_result.scalars().all()
        if not tasks:
            return []

        task_map = {t.id: t.workstream for t in tasks}
        task_ids = list(task_map.keys())

        # Fetch findings for those tasks
        findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
        findings = findings_result.scalars().all()
        if not findings:
            return []

        # Group by (severity, workstream/capability_area)
        # key: (severity, capability_area) → {workstreams: set, count: int, max_confidence: float}
        groups: dict[tuple[str, str], dict] = defaultdict(lambda: {"workstreams": set(), "count": 0, "max_confidence": 0.0})

        for f in findings:
            workstream = task_map.get(f.task_id, "general")
            capability_area = workstream if workstream else "general"
            key = (f.severity or "unknown", capability_area)
            groups[key]["workstreams"].add(workstream)
            groups[key]["count"] += 1
            groups[key]["max_confidence"] = max(groups[key]["max_confidence"], f.confidence or 0.0)

        result = []
        for (severity, capability_area), data in groups.items():
            result.append(RiskHeatmapCell(
                capability_area=capability_area,
                severity=severity,
                risk_count=data["count"],
                workstreams=sorted(data["workstreams"]),
                max_confidence=data["max_confidence"],
            ))

        return result

    except Exception:
        # Fallback: try SPARQL, return [] on failure
        try:
            rows = sparql_client.query_risk_heatmap()
        except Exception:
            rows = []
        return [RiskHeatmapCell(**r) for r in rows]


@router.get("/{assessment_id}/executive-summary", response_model=ExecutiveSummaryOut)
async def get_executive_summary(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Executive summary — orchestrator tarafından POST /reports ile yazılır."""
    result = await db.execute(
        select(Report)
        .where(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Executive summary henüz üretilmedi")

    # Risk stats from DB
    from app.models.assessment import Task
    task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
    task_ids = [t.id for t in task_result.scalars().all()]
    findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
    findings = findings_result.scalars().all()
    total_risks = len(findings)
    critical_count = sum(1 for f in findings if f.severity == "critical")

    return ExecutiveSummaryOut(
        assessment_id=str(assessment_id),
        summary=report.executive_summary or "",
        generated_at=report.created_at.isoformat(),
        total_risks=total_risks,
        critical_count=critical_count,
        dependency_count=0,
        conflict_count=0,
    )


@router.post("/{assessment_id}/generate-summary", response_model=ExecutiveSummaryOut)
async def generate_summary(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """LLM ile executive summary üret ve reports tablosuna kaydet (S9-BA-001)."""
    from app.models.assessment import Task

    # Fetch tasks
    task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
    tasks = task_result.scalars().all()
    task_ids = [t.id for t in tasks]

    # Fetch findings
    findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
    findings = findings_result.scalars().all()

    if not findings:
        raise HTTPException(status_code=422, detail="No findings found for this assessment")

    finding_ids = [f.id for f in findings]

    # Fetch risks
    risks_result = await db.execute(select(Risk).where(Risk.finding_id.in_(finding_ids)))
    risks = risks_result.scalars().all()

    # Fetch recommendations
    recs_result = await db.execute(select(Recommendation).where(Recommendation.finding_id.in_(finding_ids)))
    recs = recs_result.scalars().all()

    total_risks = len(findings)
    critical_count = sum(1 for f in findings if f.severity == "critical")

    # Build prompt
    findings_text = "\n".join(
        f"- [{f.severity.upper()}] {f.description} (confidence: {f.confidence:.2f})"
        for f in findings[:20]  # limit to avoid token overflow
    )
    risks_text = "\n".join(
        f"- [{r.level.upper()}] {r.description}"
        for r in risks[:10]
    )
    recs_text = "\n".join(
        f"- [priority {r.priority}] {r.description}"
        for r in recs[:10]
    )

    prompt = f"""You are an expert IT assessment consultant. Based on the following assessment findings, risks, and recommendations, write a concise executive summary (2-4 paragraphs) suitable for senior management. Be objective and professional.

FINDINGS ({len(findings)} total, {critical_count} critical):
{findings_text}

RISKS ({len(risks)} total):
{risks_text}

RECOMMENDATIONS ({len(recs)} total):
{recs_text}

Write the executive summary now:"""

    # Call Anthropic API or return mock
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_api_key:
        try:
            import anthropic as anthropic_sdk
            anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
            client_anthropic = anthropic_sdk.Anthropic(api_key=anthropic_api_key)
            msg = client_anthropic.messages.create(
                model=anthropic_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            summary_text = msg.content[0].text
        except Exception as exc:
            summary_text = (
                f"[Mock Summary — LLM unavailable: {exc}] "
                f"Assessment contains {total_risks} findings ({critical_count} critical), "
                f"{len(risks)} risks, and {len(recs)} recommendations."
            )
    else:
        summary_text = (
            f"[Mock Summary — ANTHROPIC_API_KEY not set] "
            f"Assessment contains {total_risks} findings ({critical_count} critical), "
            f"{len(risks)} risks, and {len(recs)} recommendations. "
            f"Key areas of concern include: "
            + ", ".join({f.severity for f in findings})
            + " severity issues."
        )

    # Save report to DB
    now = datetime.now(timezone.utc)
    report = Report(
        assessment_id=assessment_id,
        title=f"Executive Summary — {now.strftime('%Y-%m-%d %H:%M')}",
        executive_summary=summary_text,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ExecutiveSummaryOut(
        assessment_id=str(assessment_id),
        summary=summary_text,
        generated_at=report.created_at.isoformat(),
        total_risks=total_risks,
        critical_count=critical_count,
        dependency_count=0,
        conflict_count=0,
    )


@router.get("/{assessment_id}/roadmap", response_model=list[RoadmapItemOut])
async def get_consolidated_roadmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Konsolide roadmap — sadece approved recommendations (S9-BA-002)."""
    from app.models.assessment import Task
    task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
    task_ids = [t.id for t in task_result.scalars().all()]
    findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
    finding_ids = [f.id for f in findings_result.scalars().all()]

    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.finding_id.in_(finding_ids),
            Recommendation.approval_status == "approved",
        )
        .order_by(Recommendation.priority)
    )
    recs = result.scalars().all()
    return [
        RoadmapItemOut(
            id=str(r.id),
            title="",
            description=r.description or "",
            horizon="medium",
            priority=r.priority or 3,
            workstreams=[],
            effort=r.effort or "",
        )
        for r in recs
    ]


@router.get("/{assessment_id}/dependencies", response_model=list[DependencyOut])
async def get_cross_task_dependencies(assessment_id: uuid.UUID) -> list[DependencyOut]:
    """Cross-task dependency SPARQL sorgusu (S4-KA-002)."""
    try:
        rows = sparql_client.query_cross_task_dependencies()
    except Exception:
        rows = []
    return [
        DependencyOut(
            workstream_a=r.get("workstreamA", ""),
            workstream_b=r.get("workstreamB", ""),
            dependency_type=r.get("dependencyType", "explicit"),
            shared_capability_area=r.get("sharedCapabilityArea"),
            conflict_signal=r.get("conflictSignal"),
        )
        for r in rows
    ]
