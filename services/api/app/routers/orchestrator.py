# S4-AA-001..008 + S17: Orchestrator read-only endpoints
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import MaturityScore, Task
from app.models.finding import Finding, Recommendation, Report, Risk
from app.schemas.recommendation import RecommendationOut
from app.services import sparql_client
from app.services.llm_client import generate_recommendation_for_finding
from app.services.simulation_runner import build_simulation_exec_summary

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])
logger = logging.getLogger(__name__)


class RiskHeatmapCell(BaseModel):
    capability_area: str
    severity: str
    risk_count: int
    workstreams: list[str]
    max_confidence: float


class HeatmapFindingOut(BaseModel):
    id: str
    description: str
    severity: str
    confidence: float
    workstream: str
    approval_status: str


class WorkstreamSummaryOut(BaseModel):
    workstream: str
    task_status: str
    maturity_score: float | None = None
    finding_count: int = 0
    critical_count: int = 0
    high_count: int = 0


class TopRiskOut(BaseModel):
    id: str
    description: str
    severity: str
    workstream: str
    confidence: float


class TopRecommendationOut(BaseModel):
    id: str
    title: str
    description: str
    priority: int
    effort: str


class ExecutiveSummaryOut(BaseModel):
    assessment_id: str
    summary: str
    generated_at: str | None = None
    total_risks: int
    critical_count: int
    high_count: int = 0
    dependency_count: int
    conflict_count: int
    avg_maturity: float | None = None
    pending_approvals: int = 0
    tasks_completed: int = 0
    tasks_total: int = 0
    workstream_summaries: list[WorkstreamSummaryOut] = []
    top_risks: list[TopRiskOut] = []
    top_recommendations: list[TopRecommendationOut] = []


class RoadmapItemOut(BaseModel):
    id: str | None = None
    title: str
    description: str
    horizon: str
    priority: int
    workstreams: list[str]
    effort: str
    addresses_conflict: bool = False
    finding_id: str | None = None
    consolidated: bool = False


class DependencyOut(BaseModel):
    workstream_a: str
    workstream_b: str
    dependency_type: str
    shared_capability_area: str | None = None
    conflict_signal: str | None = None


class GenerateRecommendationsOut(BaseModel):
    created: int
    recommendations: list[RecommendationOut]


def _infer_horizon(priority: int | None, effort: str | None) -> str:
    effort_l = (effort or "").lower()
    p = priority or 3
    if p <= 2 or effort_l in ("low", "xs", "s"):
        return "short"
    if p >= 4 or effort_l in ("high", "xl", "large"):
        return "long"
    return "medium"


def _rec_title(description: str | None, existing: str | None = None) -> str:
    if existing and existing.strip():
        return existing.strip()
    text = (description or "").strip()
    if not text:
        return "Öneri"
    return text[:80] + ("…" if len(text) > 80 else "")


async def _assessment_context(assessment_id: uuid.UUID, db: AsyncSession):
    task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
    tasks = task_result.scalars().all()
    task_map = {t.id: t for t in tasks}
    task_ids = list(task_map.keys())

    findings: list[Finding] = []
    if task_ids:
        findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
        findings = list(findings_result.scalars().all())

    finding_ids = [f.id for f in findings]
    risks: list[Risk] = []
    recs: list[Recommendation] = []
    if finding_ids:
        risks_result = await db.execute(select(Risk).where(Risk.finding_id.in_(finding_ids)))
        risks = list(risks_result.scalars().all())
        recs_result = await db.execute(select(Recommendation).where(Recommendation.finding_id.in_(finding_ids)))
        recs = list(recs_result.scalars().all())

    maturity_result = await db.execute(
        select(MaturityScore).where(MaturityScore.assessment_id == assessment_id)
    )
    maturity_by_ws = {m.workstream: m for m in maturity_result.scalars().all()}

    return tasks, task_map, findings, risks, recs, maturity_by_ws


async def _dependency_counts(assessment_id: uuid.UUID) -> tuple[int, int]:
    try:
        rows = sparql_client.query_cross_task_dependencies()
    except Exception:
        rows = []
    dep_count = len(rows)
    conflict_count = sum(1 for r in rows if r.get("conflictSignal"))
    return dep_count, conflict_count


def _build_executive_dashboard(
    assessment_id: uuid.UUID,
    tasks: list[Task],
    task_map: dict,
    findings: list[Finding],
    recs: list[Recommendation],
    maturity_by_ws: dict[str, MaturityScore],
    summary: str = "",
    generated_at: str | None = None,
    dependency_count: int = 0,
    conflict_count: int = 0,
) -> ExecutiveSummaryOut:
    critical_count = sum(1 for f in findings if f.severity == "critical")
    high_count = sum(1 for f in findings if f.severity == "high")
    pending = sum(
        1 for x in findings + [] if getattr(x, "approval_status", None) == "pending"
    )
    # include risks/recs pending from caller if needed — computed below in async path

    ws_summaries: list[WorkstreamSummaryOut] = []
    for t in tasks:
        ws_findings = [f for f in findings if f.task_id == t.id]
        m = maturity_by_ws.get(t.workstream)
        ws_summaries.append(
            WorkstreamSummaryOut(
                workstream=t.workstream,
                task_status=t.status,
                maturity_score=float(m.score) if m else None,
                finding_count=len(ws_findings),
                critical_count=sum(1 for f in ws_findings if f.severity == "critical"),
                high_count=sum(1 for f in ws_findings if f.severity == "high"),
            )
        )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(
        findings,
        key=lambda f: (severity_order.get(f.severity or "info", 5), -(f.confidence or 0)),
    )
    top_risks = [
        TopRiskOut(
            id=str(f.id),
            description=f.description,
            severity=f.severity,
            workstream=task_map[f.task_id].workstream if f.task_id in task_map else "general",
            confidence=f.confidence or 0.0,
        )
        for f in sorted_findings[:5]
    ]

    approved_recs = [r for r in recs if r.approval_status == "approved"]
    approved_recs.sort(key=lambda r: r.priority or 99)
    top_recs = [
        TopRecommendationOut(
            id=str(r.id),
            title=_rec_title(r.description, r.title),
            description=r.description or "",
            priority=r.priority or 3,
            effort=r.effort or "",
        )
        for r in approved_recs[:5]
    ]

    scores = [float(m.score) for m in maturity_by_ws.values() if m.score is not None]
    avg_maturity = round(sum(scores) / len(scores), 2) if scores else None

    return ExecutiveSummaryOut(
        assessment_id=str(assessment_id),
        summary=summary,
        generated_at=generated_at,
        total_risks=len(findings),
        critical_count=critical_count,
        high_count=high_count,
        dependency_count=dependency_count,
        conflict_count=conflict_count,
        avg_maturity=avg_maturity,
        pending_approvals=pending,
        tasks_completed=sum(1 for t in tasks if t.status == "completed"),
        tasks_total=len(tasks),
        workstream_summaries=ws_summaries,
        top_risks=top_risks,
        top_recommendations=top_recs,
    )


@router.get("/{assessment_id}/risk-heatmap", response_model=list[RiskHeatmapCell])
async def get_risk_heatmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[RiskHeatmapCell]:
    try:
        tasks, task_map, findings, _, _, _ = await _assessment_context(assessment_id, db)
        if not tasks or not findings:
            return []

        groups: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"workstreams": set(), "count": 0, "max_confidence": 0.0}
        )
        for f in findings:
            workstream = task_map[f.task_id].workstream if f.task_id in task_map else "general"
            capability_area = workstream or "general"
            key = (f.severity or "unknown", capability_area)
            groups[key]["workstreams"].add(workstream)
            groups[key]["count"] += 1
            groups[key]["max_confidence"] = max(groups[key]["max_confidence"], f.confidence or 0.0)

        return [
            RiskHeatmapCell(
                capability_area=capability_area,
                severity=severity,
                risk_count=data["count"],
                workstreams=sorted(data["workstreams"]),
                max_confidence=data["max_confidence"],
            )
            for (severity, capability_area), data in groups.items()
        ]
    except Exception:
        try:
            rows = sparql_client.query_risk_heatmap()
        except Exception:
            rows = []
        return [RiskHeatmapCell(**r) for r in rows]


@router.get("/{assessment_id}/risk-heatmap/findings", response_model=list[HeatmapFindingOut])
async def get_heatmap_findings(
    assessment_id: uuid.UUID,
    capability_area: str = Query(...),
    severity: str = Query(...),
    approved_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    tasks, task_map, findings, _, _, _ = await _assessment_context(assessment_id, db)
    out: list[HeatmapFindingOut] = []
    for f in findings:
        ws = task_map[f.task_id].workstream if f.task_id in task_map else "general"
        if ws != capability_area or (f.severity or "") != severity:
            continue
        if approved_only and f.approval_status != "approved":
            continue
        out.append(
            HeatmapFindingOut(
                id=str(f.id),
                description=f.description,
                severity=f.severity,
                confidence=f.confidence or 0.0,
                workstream=ws,
                approval_status=f.approval_status,
            )
        )
    return out


@router.get("/{assessment_id}/executive-summary", response_model=ExecutiveSummaryOut)
async def get_executive_summary(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tasks, task_map, findings, risks, recs, maturity_by_ws = await _assessment_context(assessment_id, db)
    dep_count, conflict_count = await _dependency_counts(assessment_id)

    result = await db.execute(
        select(Report)
        .where(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()

    pending = (
        sum(1 for f in findings if f.approval_status == "pending")
        + sum(1 for r in risks if r.approval_status == "pending")
        + sum(1 for r in recs if r.approval_status == "pending")
    )

    dashboard = _build_executive_dashboard(
        assessment_id,
        tasks,
        task_map,
        findings,
        recs,
        maturity_by_ws,
        summary=report.executive_summary if report else "",
        generated_at=report.created_at.isoformat() if report else None,
        dependency_count=dep_count,
        conflict_count=conflict_count,
    )
    dashboard.pending_approvals = pending
    return dashboard


@router.post("/{assessment_id}/generate-summary", response_model=ExecutiveSummaryOut)
async def generate_summary(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        tasks, task_map, findings, risks, recs, maturity_by_ws = await _assessment_context(assessment_id, db)
        dep_count, conflict_count = await _dependency_counts(assessment_id)
        maturity_text = "\n".join(
            f"- {ws}: {m.score}/5 ({m.maturity_level})" for ws, m in maturity_by_ws.items()
        )

        if not findings:
            try:
                qa_summary = await build_simulation_exec_summary(assessment_id, db)
            except Exception:
                qa_summary = "Değerlendirme özeti henüz oluşturulamadı."
            if not (qa_summary or "").strip():
                qa_summary = (
                    "[Mock Summary] Bu assessment için henüz değerlendirilmiş yanıt veya bulgu yok."
                )
            summary_parts = [qa_summary]
            if maturity_text:
                summary_parts.append(f"\n\nOlgunluk Skorları:\n{maturity_text}")
            summary_text = "\n".join(summary_parts).strip()
        else:
            total_risks = len(findings)
            critical_count = sum(1 for f in findings if f.severity == "critical")

            findings_text = "\n".join(
                f"- [{f.severity.upper()}] {f.description} (confidence: {f.confidence:.2f})"
                for f in findings[:20]
            )
            risks_text = "\n".join(f"- [{r.level.upper()}] {r.description}" for r in risks[:10])
            recs_text = "\n".join(f"- [priority {r.priority}] {r.description}" for r in recs[:10])

            prompt = f"""You are an expert IT assessment consultant. Write a concise executive summary (2-4 paragraphs) for senior management.

FINDINGS ({total_risks} total, {critical_count} critical):
{findings_text}

RISKS ({len(risks)} total):
{risks_text}

RECOMMENDATIONS ({len(recs)} total):
{recs_text}

MATURITY:
{maturity_text or 'No maturity scores yet.'}

Write the executive summary now:"""

            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_api_key:
                try:
                    import anthropic as anthropic_sdk
                    client_anthropic = anthropic_sdk.Anthropic(api_key=anthropic_api_key)
                    msg = client_anthropic.messages.create(
                        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    summary_text = msg.content[0].text
                except Exception as exc:
                    summary_text = (
                        f"[Mock Summary — LLM unavailable: {exc}] "
                        f"Assessment contains {total_risks} findings ({critical_count} critical)."
                    )
            else:
                summary_text = (
                    f"[Mock Summary] Assessment contains {total_risks} findings ({critical_count} critical), "
                    f"{len(risks)} risks, and {len(recs)} recommendations."
                )

        now = datetime.now(timezone.utc)
        report = Report(
            assessment_id=assessment_id,
            title=f"Executive Summary — {now.strftime('%Y-%m-%d %H:%M')}",
            executive_summary=summary_text,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        dashboard = _build_executive_dashboard(
            assessment_id,
            tasks,
            task_map,
            findings,
            recs,
            maturity_by_ws,
            summary=summary_text,
            generated_at=report.created_at.isoformat(),
            dependency_count=dep_count,
            conflict_count=conflict_count,
        )
        pending = (
            sum(1 for f in findings if f.approval_status == "pending")
            + sum(1 for r in risks if r.approval_status == "pending")
            + sum(1 for r in recs if r.approval_status == "pending")
        )
        dashboard.pending_approvals = pending
        return dashboard
    except Exception as exc:
        logger.exception("generate-summary failed for %s: %s", assessment_id, exc)
        mock_summary = f"[Mock Summary — generation failed: {exc}]"
        try:
            tasks, task_map, findings, risks, recs, maturity_by_ws = await _assessment_context(assessment_id, db)
            dep_count, conflict_count = await _dependency_counts(assessment_id)
        except Exception:
            tasks, task_map, findings, recs, maturity_by_ws = [], {}, [], [], []
            dep_count, conflict_count = 0, 0
        dashboard = _build_executive_dashboard(
            assessment_id,
            tasks,
            task_map,
            findings,
            recs,
            maturity_by_ws,
            summary=mock_summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
            dependency_count=dep_count,
            conflict_count=conflict_count,
        )
        return dashboard


def _roadmap_item_from_rec(rec: Recommendation, workstream: str, conflict_ws: set[tuple[str, str]]) -> RoadmapItemOut:
    horizon = rec.horizon or _infer_horizon(rec.priority, rec.effort)
    title = _rec_title(rec.description, rec.title)
    addresses = any(
        workstream in (a, b) for a, b in conflict_ws
    )
    return RoadmapItemOut(
        id=str(rec.id),
        title=title,
        description=rec.description or "",
        horizon=horizon,
        priority=rec.priority or 3,
        workstreams=[workstream] if workstream else [],
        effort=rec.effort or "",
        addresses_conflict=addresses,
        finding_id=str(rec.finding_id),
    )


@router.get("/{assessment_id}/roadmap", response_model=list[RoadmapItemOut])
async def get_consolidated_roadmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tasks, task_map, findings, _, _, _ = await _assessment_context(assessment_id, db)
    finding_ws = {f.id: task_map[f.task_id].workstream for f in findings if f.task_id in task_map}
    finding_ids = list(finding_ws.keys())

    if not finding_ids:
        return []

    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.finding_id.in_(finding_ids),
            Recommendation.approval_status == "approved",
        )
        .order_by(Recommendation.priority)
    )
    recs = result.scalars().all()

    try:
        dep_rows = sparql_client.query_cross_task_dependencies()
    except Exception:
        dep_rows = []
    conflict_pairs = {
        (r.get("workstreamA", ""), r.get("workstreamB", ""))
        for r in dep_rows
        if r.get("conflictSignal")
    }

    return [
        _roadmap_item_from_rec(r, finding_ws.get(r.finding_id, ""), conflict_pairs)
        for r in recs
    ]


@router.post("/{assessment_id}/generate-roadmap", response_model=list[RoadmapItemOut])
async def generate_roadmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Infer title/horizon on approved recommendations."""
    tasks, task_map, findings, _, _, _ = await _assessment_context(assessment_id, db)
    finding_ids = [f.id for f in findings]
    if not finding_ids:
        return []

    result = await db.execute(
        select(Recommendation).where(
            Recommendation.finding_id.in_(finding_ids),
            Recommendation.approval_status == "approved",
        )
    )
    recs = result.scalars().all()
    for rec in recs:
        if not rec.title:
            rec.title = _rec_title(rec.description)
        if not rec.horizon:
            rec.horizon = _infer_horizon(rec.priority, rec.effort)
    await db.commit()
    return await get_consolidated_roadmap(assessment_id, db)


@router.post("/{assessment_id}/generate-recommendations", response_model=GenerateRecommendationsOut)
async def generate_recommendations(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Create recommendations for approved findings that lack one."""
    tasks, task_map, findings, _, existing_recs, _ = await _assessment_context(assessment_id, db)
    if not findings:
        return GenerateRecommendationsOut(created=0, recommendations=[])

    finding_ids_with_recs = {r.finding_id for r in existing_recs}
    targets = [
        f for f in findings
        if f.approval_status == "approved" and f.id not in finding_ids_with_recs
    ]

    created: list[Recommendation] = []
    for finding in targets:
        workstream = task_map[finding.task_id].workstream if finding.task_id in task_map else ""
        generated = generate_recommendation_for_finding(
            finding.description,
            finding.severity or "medium",
            workstream,
        )
        rec = Recommendation(
            finding_id=finding.id,
            description=generated["description"],
            priority=generated.get("priority", 3),
            effort=generated.get("effort", "medium"),
            title=_rec_title(generated["description"]),
        )
        db.add(rec)
        created.append(rec)

    if created:
        await db.commit()
        for rec in created:
            await db.refresh(rec)

    return GenerateRecommendationsOut(created=len(created), recommendations=created)


@router.get("/{assessment_id}/dependencies", response_model=list[DependencyOut])
async def get_cross_task_dependencies(assessment_id: uuid.UUID) -> list[DependencyOut]:
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
