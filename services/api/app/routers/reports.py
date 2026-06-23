import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.metrics import evidence_coverage_score
from app.models.finding import Report
from app.schemas.report import (
    ConsultantReviewRequest,
    ConsultantReviewResponse,
    ReportAiEditRequest,
    ReportAiEditResponse,
    ReportAiGenerateRequest,
    ReportAiGenerateResponse,
    ReportCreate,
    ReportOut,
    ReportUpdate,
)
from app.services.llm_client import check_consultant_comment_consistency, report_section_ai_edit
from app.services.output_validator import anonymize_report_pii, validate_evidence_chain
from app.services.report_ai import build_assessment_context, generate_sections
from app.services.report_content import compose_assessment_report, dump_content_json, parse_content_json
from app.services.report_export import content_to_html, export_docx_bytes, export_pdf_bytes

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump()
    validation = await validate_evidence_chain(str(data.get("assessment_id", "")), db)
    total = validation["total_findings"]
    covered = total - len(validation["uncovered_findings"])
    if total > 0:
        evidence_coverage_score.labels(assessment_id=str(data.get("assessment_id", ""))).set(
            covered / total
        )
    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Report blocked: findings without evidence detected",
                "uncovered_findings": validation["uncovered_findings"],
            },
        )
    if data.get("executive_summary"):
        data["executive_summary"] = await anonymize_report_pii(data["executive_summary"])
    report = Report(**data)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/assessment/{assessment_id}/compose", response_model=ReportOut)
async def compose_report(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """S18: Build content_json from orchestrator data; create or refresh latest report."""
    try:
        composed = await compose_assessment_report(assessment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = await db.execute(
        select(Report)
        .where(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    content_str = dump_content_json(composed["content"])

    if report:
        report.title = composed["title"]
        if composed["executive_summary"]:
            report.executive_summary = composed["executive_summary"]
        report.content_json = content_str
    else:
        report = Report(
            assessment_id=assessment_id,
            title=composed["title"],
            executive_summary=composed["executive_summary"] or None,
            content_json=content_str,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
async def list_reports(
    assessment_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).order_by(Report.created_at.desc())
    if assessment_id:
        q = q.where(Report.assessment_id == assessment_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportOut)
async def update_report(
    report_id: uuid.UUID,
    body: ReportUpdate,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "executive_summary" and value:
            value = await anonymize_report_pii(value)
        setattr(report, field, value)
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/{report_id}/ai-edit", response_model=ReportAiEditResponse)
async def ai_edit_report(
    report_id: uuid.UUID,
    body: ReportAiEditRequest,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = parse_content_json(report.content_json)
    sections = content.get("sections", [])
    target_ids: list[str] = []
    if body.section_id:
        target_ids = [body.section_id]
    else:
        target_ids = [s["id"] for s in sections if s.get("type") == "text" and s.get("id")]

    updated: list[str] = []
    for section in sections:
        sid = section.get("id")
        if sid not in target_ids:
            continue
        stype = section.get("type")
        if stype == "text":
            section["body"] = report_section_ai_edit(
                section_type="text",
                content=section.get("body", ""),
                instruction=body.instruction,
                mode=body.mode,
            )
            updated.append(sid)
        elif stype == "table" and body.section_id:
            rows_text = json.dumps(section.get("rows", []), ensure_ascii=False)
            new_rows = report_section_ai_edit(
                section_type="table",
                content=rows_text,
                instruction=body.instruction,
                mode=body.mode,
            )
            try:
                section["rows"] = json.loads(new_rows)
            except json.JSONDecodeError:
                pass
            updated.append(sid)

    if not updated:
        raise HTTPException(status_code=422, detail="No editable sections matched")

    report.content_json = dump_content_json(content)
    await db.commit()
    await db.refresh(report)
    return ReportAiEditResponse(
        report_id=report.id,
        updated_sections=updated,
        content_json=report.content_json or "",
    )


@router.post("/{report_id}/ai-generate", response_model=ReportAiGenerateResponse)
async def ai_generate_report(
    report_id: uuid.UUID,
    body: ReportAiGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = parse_content_json(report.content_json)
    sections = content.get("sections", [])
    assessment_context = await build_assessment_context(report.assessment_id, db)

    target_ids = [body.section_id] if body.section_id else None
    updated = generate_sections(
        sections,
        assessment_context,
        section_ids=target_ids,
        instruction=body.instruction,
        mode=body.mode,
    )

    if not updated:
        raise HTTPException(status_code=422, detail="No sections matched for AI generation")

    report.content_json = dump_content_json(content)
    await db.commit()
    await db.refresh(report)
    return ReportAiGenerateResponse(
        report_id=report.id,
        updated_sections=updated,
        content_json=report.content_json or "",
        total_sections=len(updated),
    )


def _section_text_for_review(section: dict) -> str:
    stype = section.get("type", "text")
    if stype == "text":
        return section.get("body", "") or ""
    if stype == "table":
        return json.dumps(
            {"columns": section.get("columns", []), "rows": section.get("rows", [])},
            ensure_ascii=False,
        )
    if section.get("commentary"):
        return section["commentary"]
    return json.dumps(section.get("data", {}), ensure_ascii=False)


@router.post("/{report_id}/consultant-review", response_model=ConsultantReviewResponse)
async def consultant_review_section(
    report_id: uuid.UUID,
    body: ConsultantReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = parse_content_json(report.content_json)
    sections = content.get("sections", [])
    target = next((s for s in sections if s.get("id") == body.section_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Section not found")

    section_text = _section_text_for_review(target)
    check = check_consultant_comment_consistency(
        target.get("title") or body.section_id,
        section_text,
        body.consultant_comment,
    )

    target["consultant_comment"] = body.consultant_comment
    if body.consultant_comment.strip():
        target["consultant_approved"] = bool(check.get("consistent", True))

    report.content_json = dump_content_json(content)
    await db.commit()
    await db.refresh(report)

    return ConsultantReviewResponse(
        report_id=report.id,
        section_id=body.section_id,
        consistent=bool(check.get("consistent", True)),
        feedback=str(check.get("feedback", "")),
        content_json=report.content_json or "",
    )


async def _export_evidence_guard(report: Report, force: bool, db: AsyncSession) -> None:
    validation = await validate_evidence_chain(str(report.assessment_id), db)
    if not validation["valid"] and not force:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Export blocked: findings without evidence. Use force=true to override.",
                "uncovered_findings": validation["uncovered_findings"],
            },
        )


@router.post("/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: uuid.UUID,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await _export_evidence_guard(report, force, db)
    html_doc = content_to_html(report.title, report.content_json)
    pdf_bytes = export_pdf_bytes(html_doc)
    media = "application/pdf" if pdf_bytes[:4] == b"%PDF" else "text/html"
    ext = "pdf" if media == "application/pdf" else "html"
    return Response(
        content=pdf_bytes,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.{ext}"'},
    )


@router.post("/{report_id}/export/docx")
async def export_report_docx(
    report_id: uuid.UUID,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await _export_evidence_guard(report, force, db)
    docx_bytes = export_docx_bytes(report.title, report.content_json)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.docx"'},
    )
