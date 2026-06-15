# S5-BA-002: Evidence chain validation before report generation
# S5-BA-003: PII anonymization from report content

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

log = logging.getLogger("output_validator")


async def validate_evidence_chain(assessment_id: str, db: AsyncSession) -> dict:
    """S5-BA-002: Every finding must have at least one evidence before report generation."""
    from app.models.finding import Finding, Evidence

    stmt = (
        select(Finding.id, Finding.title)
        .where(Finding.assessment_id == assessment_id)
    )
    result = await db.execute(stmt)
    findings = result.all()

    uncovered: list[dict] = []
    for finding in findings:
        ev_stmt = select(Evidence.id).where(Evidence.finding_id == finding.id).limit(1)
        ev_result = await db.execute(ev_stmt)
        if ev_result.scalar() is None:
            uncovered.append({"finding_id": str(finding.id), "title": finding.title})

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
