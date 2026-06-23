"""Assessment Results View — composite Gold data product for chat and agents."""
from __future__ import annotations

import uuid
from pathlib import Path

import yaml
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.routers.orchestrator import (
    TopRecommendationOut,
    TopRiskOut,
    WorkstreamSummaryOut,
    _assessment_context,
    _build_executive_dashboard,
    _dependency_counts,
)


class AssessmentResultsKpi(BaseModel):
    total_findings: int
    critical_count: int
    high_count: int
    avg_maturity: float | None
    tasks_completed: int
    tasks_total: int
    pending_approvals: int
    dependency_count: int
    conflict_count: int


class AssessmentResultsView(BaseModel):
    product_id: str = "assessment_results_view"
    assessment_id: str
    client_name: str
    project_name: str
    status: str
    assessment_mode: str | None = None
    simulation_status: str | None = None
    summary: str
    kpis: AssessmentResultsKpi
    workstreams: list[WorkstreamSummaryOut]
    top_findings: list[TopRiskOut]
    top_recommendations: list[TopRecommendationOut]


def _catalog_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "data_products_catalog.yaml",
        Path(__file__).resolve().parents[4] / "knowledge" / "architecture" / "data_products_catalog.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def load_data_products_catalog() -> dict:
    path = _catalog_path()
    if not path.exists():
        return {"version": "1.0", "products": [], "containers": []}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


async def compose_assessment_results_view(
    assessment_id: uuid.UUID,
    db: AsyncSession,
) -> AssessmentResultsView:
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError("Assessment not found")

    tasks, task_map, findings, _risks, recs, maturity_by_ws = await _assessment_context(assessment_id, db)
    dep_count, conflict_count = await _dependency_counts(assessment_id)

    from app.models.finding import Report
    from sqlalchemy import select

    report_result = await db.execute(
        select(Report)
        .where(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = report_result.scalar_one_or_none()

    dashboard = _build_executive_dashboard(
        assessment_id,
        tasks,
        task_map,
        findings,
        recs,
        maturity_by_ws,
        summary=report.executive_summary if report else "",
        dependency_count=dep_count,
        conflict_count=conflict_count,
    )

    return AssessmentResultsView(
        assessment_id=str(assessment_id),
        client_name=assessment.client_name,
        project_name=assessment.project_name,
        status=assessment.status,
        assessment_mode=assessment.assessment_mode,
        simulation_status=assessment.simulation_status,
        summary=dashboard.summary or "",
        kpis=AssessmentResultsKpi(
            total_findings=dashboard.total_risks,
            critical_count=dashboard.critical_count,
            high_count=dashboard.high_count,
            avg_maturity=dashboard.avg_maturity,
            tasks_completed=dashboard.tasks_completed,
            tasks_total=dashboard.tasks_total,
            pending_approvals=dashboard.pending_approvals,
            dependency_count=dashboard.dependency_count,
            conflict_count=dashboard.conflict_count,
        ),
        workstreams=dashboard.workstream_summaries,
        top_findings=dashboard.top_risks,
        top_recommendations=dashboard.top_recommendations,
    )


def format_assessment_results_for_llm(view: AssessmentResultsView) -> str:
    """Turkish text block injected into chat / agent context."""
    lines = [
        f"=== Assessment Results View (data product: {view.product_id}) ===",
        f"Müşteri: {view.client_name} — Proje: {view.project_name}",
        f"Durum: {view.status}"
        + (f" | Simülasyon: {view.simulation_status}" if view.simulation_status else ""),
        "",
        "KPI:",
        f"- Toplam bulgu: {view.kpis.total_findings}",
        f"- Kritik: {view.kpis.critical_count} | Yüksek: {view.kpis.high_count}",
        f"- Olgunluk ort.: {view.kpis.avg_maturity if view.kpis.avg_maturity is not None else '—'}",
        f"- Task: {view.kpis.tasks_completed}/{view.kpis.tasks_total}",
        f"- Onay bekleyen: {view.kpis.pending_approvals}",
    ]
    if view.summary.strip():
        lines.extend(["", "Yönetici özeti:", view.summary.strip()[:1200]])

    if view.workstreams:
        lines.extend(["", "Workstream özeti:"])
        for ws in view.workstreams:
            mat = f"{ws.maturity_score:.1f}" if ws.maturity_score is not None else "—"
            lines.append(
                f"- {ws.workstream}: olgunluk={mat}, bulgu={ws.finding_count}, "
                f"kritik={ws.critical_count}, durum={ws.task_status}"
            )

    if view.top_findings:
        lines.extend(["", "Öne çıkan bulgular:"])
        for i, f in enumerate(view.top_findings[:5], 1):
            lines.append(f"{i}. [{f.severity}] {f.workstream}: {f.description[:160]}")

    if view.top_recommendations:
        lines.extend(["", "Öne çıkan öneriler:"])
        for i, r in enumerate(view.top_recommendations[:3], 1):
            lines.append(f"{i}. (P{r.priority}) {r.title}: {r.description[:120]}")

    return "\n".join(lines)
