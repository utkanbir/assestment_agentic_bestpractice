# S5-BA-002: Evidence chain validation before report generation
# S5-BA-003: PII anonymization from report content

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

log = logging.getLogger("output_validator")


async def validate_evidence_chain(assessment_id: str, db: AsyncSession) -> dict:
    """S5-BA-002 / S18: Every finding must link to evidence via task assessment."""
    from app.models.finding import Finding, Evidence
    from app.models.assessment import Task

    aid = uuid.UUID(assessment_id) if isinstance(assessment_id, str) else assessment_id
    task_result = await db.execute(select(Task.id).where(Task.assessment_id == aid))
    task_ids = [row[0] for row in task_result.all()]
    if not task_ids:
        return {"valid": True, "total_findings": 0, "uncovered_findings": []}

    stmt = select(Finding.id, Finding.description, Finding.evidence_id).where(Finding.task_id.in_(task_ids))
    result = await db.execute(stmt)
    findings = result.all()

    uncovered: list[dict] = []
    for finding in findings:
        if finding.evidence_id:
            ev_stmt = select(Evidence.id).where(Evidence.id == finding.evidence_id).limit(1)
            ev_result = await db.execute(ev_stmt)
            if ev_result.scalar() is not None:
                continue
        uncovered.append({
            "finding_id": str(finding.id),
            "title": (finding.description or "")[:80],
        })

    return {
        "valid": len(uncovered) == 0,
        "total_findings": len(findings),
        "uncovered_findings": uncovered,
    }


async def anonymize_report_pii(content: str) -> str:
    """S5-BA-003: Strip PII from report text before storing/returning."""
    try:
        from services.presidio.pii_client import anonymize
        return await anonymize(content, language="tr")
    except Exception:
        # Presidio unavailable — log but do not block report
        log.warning("PII anonymization unavailable, report stored as-is")
        return content
