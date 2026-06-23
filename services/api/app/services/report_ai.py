"""S20: AI report section generation with assessment context."""
import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.routers.orchestrator import (
    _assessment_context,
    _build_executive_dashboard,
    _dependency_counts,
    get_consolidated_roadmap,
)
from app.services.llm_client import report_section_ai_generate


async def build_assessment_context(assessment_id: uuid.UUID, db: AsyncSession) -> str:
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        return ""

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
    roadmap = await get_consolidated_roadmap(assessment_id, db)

    maturity_lines = [
        f"- {ws}: {m.score}/5" for ws, m in maturity_by_ws.items()
    ] or ["- Olgunluk verisi yok"]
    risk_lines = [
        f"- [{r.severity}] {r.workstream}: {r.description[:120]}"
        for r in dashboard.top_risks[:5]
    ] or ["- Kritik bulgu yok"]
    roadmap_lines = [
        f"- {item.title} ({item.horizon}, P{item.priority})"
        for item in roadmap[:5]
    ] or ["- Roadmap öğesi yok"]

    return f"""Müşteri: {assessment.client_name}
Proje: {assessment.project_name}
Toplam bulgu: {dashboard.total_risks}
Kritik: {dashboard.critical_count} | Yüksek: {dashboard.high_count}
Ortalama olgunluk: {dashboard.avg_maturity if dashboard.avg_maturity else '—'}
Task durumu: {dashboard.tasks_completed}/{dashboard.tasks_total}

Olgunluk:
{chr(10).join(maturity_lines)}

Öne çıkan riskler:
{chr(10).join(risk_lines)}

Roadmap özeti:
{chr(10).join(roadmap_lines)}"""


def _section_payload(section: dict) -> str:
    stype = section.get("type", "text")
    if stype == "text":
        return section.get("body", "") or ""
    if stype == "table":
        return json.dumps(
            {"columns": section.get("columns", []), "rows": section.get("rows", [])},
            ensure_ascii=False,
        )
    if stype in ("chart_radar", "chart_heatmap", "kpi_grid"):
        return json.dumps(
            {
                "title": section.get("title", ""),
                "data": section.get("data", {}),
                "items": section.get("items", []),
                "commentary": section.get("commentary", ""),
            },
            ensure_ascii=False,
        )
    if stype == "cover":
        return json.dumps(
            {
                "title": section.get("title", ""),
                "client": section.get("client", ""),
                "project": section.get("project", ""),
                "subtitle": section.get("subtitle", ""),
            },
            ensure_ascii=False,
        )
    return json.dumps(section, ensure_ascii=False)


def _mock_section_output(section: dict, context: str) -> dict[str, Any]:
    stype = section.get("type", "text")
    title = section.get("title", section.get("id", "Bölüm"))
    client = ""
    for line in context.splitlines():
        if line.startswith("Müşteri:"):
            client = line.split(":", 1)[-1].strip()
            break

    if stype == "text":
        return {
            "body": (
                f"{title}: {client} değerlendirmesi kapsamında bu bölüm, mevcut bulgu ve olgunluk "
                f"verilerine dayanarak hazırlanmıştır. Detaylar aşağıdaki tablo ve grafiklerle desteklenmektedir."
            )
        }
    if stype == "table":
        rows = section.get("rows", [])
        if not rows:
            rows = [["—", "—", "Veri henüz oluşturulmadı"]]
        return {"rows": rows}
    if stype == "cover":
        return {"subtitle": f"{client} için konsolide değerlendirme özeti"}
    commentary = (
        f"{title} bölümü, assessment verilerine göre özetlendi. "
        f"Grafikteki değerler workstream bazlı performansı yansıtır."
    )
    return {"commentary": commentary}


def apply_generation_to_section(section: dict, result: dict[str, Any]) -> None:
    stype = section.get("type", "text")
    if stype == "text" and "body" in result:
        section["body"] = result["body"]
    elif stype == "table" and "rows" in result:
        section["rows"] = result["rows"]
    elif stype == "cover":
        if "subtitle" in result:
            section["subtitle"] = result["subtitle"]
    elif "commentary" in result:
        section["commentary"] = result["commentary"]


def generate_section_content(
    section: dict,
    assessment_context: str,
    instruction: str = "Bu bölüm için profesyonel rapor metni yaz",
    mode: str = "generate",
) -> dict[str, Any]:
    stype = section.get("type", "text")
    title = section.get("title", section.get("id", ""))
    payload = _section_payload(section)

    generated = report_section_ai_generate(
        section_type=stype,
        section_title=title,
        section_data=payload,
        assessment_context=assessment_context,
        instruction=instruction,
        mode=mode,
    )

    if not generated:
        return _mock_section_output(section, assessment_context)

    if stype == "text":
        return {"body": generated}
    if stype == "table":
        try:
            parsed = json.loads(generated)
            if isinstance(parsed, list):
                return {"rows": parsed}
            if isinstance(parsed, dict) and "rows" in parsed:
                return {"rows": parsed["rows"]}
        except json.JSONDecodeError:
            pass
        return _mock_section_output(section, assessment_context)
    if stype == "cover":
        return {"subtitle": generated[:200]}
    return {"commentary": generated}


def generate_sections(
    sections: list[dict],
    assessment_context: str,
    section_ids: list[str] | None = None,
    instruction: str = "Bu bölüm için profesyonel rapor metni yaz",
    mode: str = "generate",
) -> list[str]:
    targets = section_ids or [s.get("id") for s in sections if s.get("id")]
    updated: list[str] = []
    for section in sections:
        sid = section.get("id")
        if sid not in targets:
            continue
        stype = section.get("type")
        if stype in ("divider",):
            continue
        result = generate_section_content(section, assessment_context, instruction, mode)
        apply_generation_to_section(section, result)
        updated.append(sid)
    return updated
