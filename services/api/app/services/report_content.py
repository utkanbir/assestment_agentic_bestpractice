"""S18: Structured report content_json compose and helpers."""
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.routers.orchestrator import (
    _assessment_context,
    _build_executive_dashboard,
    _dependency_counts,
    get_consolidated_roadmap,
    get_risk_heatmap,
)


def parse_content_json(raw: str | None) -> dict:
    if not raw:
        return {"version": 1, "sections": []}
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "sections" in data:
            return data
    except json.JSONDecodeError:
        pass
    return {"version": 1, "sections": []}


def dump_content_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


async def compose_assessment_report(assessment_id: uuid.UUID, db: AsyncSession) -> dict:
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError("Assessment not found")

    tasks, task_map, findings, risks, recs, maturity_by_ws = await _assessment_context(assessment_id, db)
    dep_count, conflict_count = await _dependency_counts(assessment_id)
    dashboard = _build_executive_dashboard(
        assessment_id,
        tasks,
        task_map,
        findings,
        recs,
        maturity_by_ws,
        summary="",
        generated_at=None,
        dependency_count=dep_count,
        conflict_count=conflict_count,
    )
    heatmap = await get_risk_heatmap(assessment_id, db)
    roadmap = await get_consolidated_roadmap(assessment_id, db)
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    kpi_items = [
        {"label": "Toplam Bulgu", "value": str(dashboard.total_risks)},
        {"label": "Kritik", "value": str(dashboard.critical_count)},
        {"label": "Yüksek", "value": str(dashboard.high_count)},
        {"label": "Olgunluk Ort.", "value": f"{dashboard.avg_maturity:.1f}" if dashboard.avg_maturity else "—"},
        {"label": "Onay Bekleyen", "value": str(dashboard.pending_approvals)},
        {"label": "Task", "value": f"{dashboard.tasks_completed}/{dashboard.tasks_total}"},
    ]

    maturity_data = {
        "labels": list(maturity_by_ws.keys()),
        "values": [float(m.score) for m in maturity_by_ws.values()],
    }

    heatmap_data = {
        "cells": [c.model_dump() for c in heatmap],
    }

    ws_columns = ["Workstream", "Olgunluk", "Bulgu", "Kritik", "Durum"]
    ws_rows = [
        [
            ws.workstream,
            f"{ws.maturity_score:.1f}" if ws.maturity_score is not None else "—",
            str(ws.finding_count),
            str(ws.critical_count),
            ws.task_status,
        ]
        for ws in dashboard.workstream_summaries
    ]

    risk_columns = ["Severity", "Workstream", "Açıklama"]
    risk_rows = [
        [r.severity.upper(), r.workstream, r.description[:200]]
        for r in dashboard.top_risks
    ]

    roadmap_columns = ["Başlık", "Horizon", "Öncelik", "Efor", "Workstream"]
    roadmap_rows = [
        [
            item.title,
            item.horizon,
            f"P{item.priority}",
            item.effort or "—",
            ", ".join(item.workstreams),
        ]
        for item in roadmap
    ]

    sections = [
        {
            "id": "cover",
            "type": "cover",
            "title": f"{assessment.client_name} — {assessment.project_name}",
            "client": assessment.client_name,
            "project": assessment.project_name,
            "date": now,
        },
        {
            "id": "exec",
            "type": "text",
            "title": "Yönetici Özeti",
            "body": dashboard.summary or "Özet henüz oluşturulmadı. Yönetici Özeti sayfasından üretebilir veya burada düzenleyebilirsiniz.",
        },
        {"id": "kpi", "type": "kpi_grid", "title": "Özet Göstergeler", "items": kpi_items},
        {"id": "maturity", "type": "chart_radar", "title": "Olgunluk Profili", "data": maturity_data},
        {"id": "heatmap", "type": "chart_heatmap", "title": "Risk Heatmap", "data": heatmap_data},
        {"id": "ws_table", "type": "table", "title": "Workstream Özeti", "columns": ws_columns, "rows": ws_rows},
        {"id": "risks", "type": "table", "title": "Kritik Bulgular", "columns": risk_columns, "rows": risk_rows},
        {"id": "roadmap", "type": "table", "title": "Dönüşüm Roadmap", "columns": roadmap_columns, "rows": roadmap_rows},
        {"id": "notes", "type": "text", "title": "Danışman Notları", "body": ""},
    ]

    title = f"Assessment Raporu — {assessment.client_name} ({now})"
    return {
        "title": title,
        "executive_summary": dashboard.summary or "",
        "content": {"version": 1, "sections": sections},
    }
