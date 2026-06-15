# S4-AA-001..008: Orchestrator read-only endpoints (frontend için)
# Orchestrator'ın ürettiği sonuçlar PostgreSQL'deki reports tablosundan ve
# SPARQL endpoint'inden okunur — orchestrator bu endpoint'lere yazmaz, sadece okur.
import uuid

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
async def get_risk_heatmap(assessment_id: uuid.UUID) -> list[RiskHeatmapCell]:
    """SPARQL risk heatmap sorgusu (S4-KA-003)."""
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


@router.get("/{assessment_id}/roadmap", response_model=list[RoadmapItemOut])
async def get_consolidated_roadmap(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Konsolide roadmap — findings üzerinden join ile Recommendation listesi."""
    from app.models.assessment import Task
    task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
    task_ids = [t.id for t in task_result.scalars().all()]
    findings_result = await db.execute(select(Finding).where(Finding.task_id.in_(task_ids)))
    finding_ids = [f.id for f in findings_result.scalars().all()]

    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.finding_id.in_(finding_ids))
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
