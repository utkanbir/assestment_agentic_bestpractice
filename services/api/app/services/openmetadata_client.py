"""OpenMetadata API client — S3-BA-002/003.

Responsibilities:
  - Register custom entity type AssessmentFinding (S3-BA-002)
  - Publish lineage: data source → finding → report (S3-BA-003)
  - Create/update AssessmentFinding entities for catalog visibility

OpenMetadata REST API base: http://aakp-openmetadata.aakp-information.svc.cluster.local:8585/api/v1
"""
import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_OM_BASE = getattr(settings, "openmetadata_url",
                   "http://aakp-openmetadata.aakp-information.svc.cluster.local:8585")
_OM_API = f"{_OM_BASE}/api/v1"

# OpenMetadata basic auth (dev: admin/admin)
_OM_AUTH = ("admin", "admin")

# Custom type definition for AssessmentFinding
_CUSTOM_TYPE_PAYLOAD = {
    "name": "assessmentFinding",
    "displayName": "Assessment Finding",
    "description": "AAKP assessment sürecinde tespit edilen teknik bulgu",
    "category": "DATA_QUALITY",
    "schema": {
        "type": "object",
        "properties": {
            "severity": {
                "type": "string",
                "enum": ["critical", "high", "medium", "low", "info"],
                "description": "Bulgu şiddet seviyesi"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "LLM tarafından hesaplanan güven skoru"
            },
            "workstream": {
                "type": "string",
                "description": "Değerlendirme iş akışı (kubernetes, ingestion, vb.)"
            },
            "evidenceId": {
                "type": "string",
                "description": "Kanıt UUID (PostgreSQL)"
            },
            "taskId": {
                "type": "string",
                "description": "Task UUID (PostgreSQL)"
            },
            "kgUri": {
                "type": "string",
                "description": "Fuseki knowledge graph URI"
            }
        },
        "required": ["severity", "workstream"]
    }
}


async def _om_request(
    method: str,
    path: str,
    json_body: dict | None = None,
) -> dict | None:
    try:
        async with httpx.AsyncClient(base_url=_OM_API, auth=_OM_AUTH, timeout=15) as client:
            resp = await client.request(method, path, json=json_body)
            if resp.status_code in (200, 201):
                return resp.json()
            logger.warning("OpenMetadata %s %s → %s: %s", method, path, resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("OpenMetadata unavailable (%s %s): %s", method, path, exc)
    return None


async def ensure_custom_type() -> dict | None:
    """S3-BA-002: Register AssessmentFinding custom type in OpenMetadata catalog.
    Idempotent — PUT upserts.
    """
    return await _om_request("PUT", "/metadata/types", json_body=_CUSTOM_TYPE_PAYLOAD)


async def create_finding_entity(
    finding_id: uuid.UUID,
    description: str,
    severity: str,
    confidence: float,
    workstream: str,
    task_id: uuid.UUID,
    evidence_id: uuid.UUID | None = None,
    kg_uri: str | None = None,
) -> dict | None:
    """S3-BA-002: Publish an assessment finding to OpenMetadata catalog."""
    payload = {
        "name": str(finding_id),
        "displayName": f"[{severity.upper()}] {description[:80]}",
        "description": description,
        "entityType": "assessmentFinding",
        "extension": {
            "severity": severity,
            "confidence": confidence,
            "workstream": workstream,
            "taskId": str(task_id),
            "evidenceId": str(evidence_id) if evidence_id else None,
            "kgUri": kg_uri,
        },
        "tags": [
            {"tagFQN": f"aakp.{severity}"},
            {"tagFQN": f"aakp.workstream.{workstream}"},
        ],
    }
    return await _om_request("PUT", "/dataQuality/testCases", json_body=payload)


async def add_lineage(
    from_entity_type: str,
    from_fqn: str,
    to_entity_type: str,
    to_fqn: str,
    description: str = "",
) -> dict | None:
    """S3-BA-003: Add lineage edge in OpenMetadata.

    Example:
      add_lineage("table", "teradata.schema.orders", "dataQuality/testCase", "finding-uuid")
    """
    payload: dict[str, Any] = {
        "edge": {
            "fromEntity": {"type": from_entity_type, "fullyQualifiedName": from_fqn},
            "toEntity": {"type": to_entity_type, "fullyQualifiedName": to_fqn},
            "lineageDetails": {
                "description": description,
                "source": "Manual",
            },
        }
    }
    return await _om_request("PUT", "/lineage", json_body=payload)


async def add_finding_lineage(
    finding_id: uuid.UUID,
    source_table_fqn: str,
    workstream: str,
) -> dict | None:
    """S3-BA-003: Link source data table → AssessmentFinding lineage."""
    return await add_lineage(
        from_entity_type="table",
        from_fqn=source_table_fqn,
        to_entity_type="dataQuality/testCase",
        to_fqn=str(finding_id),
        description=f"AAKP {workstream} assessment finding derived from source data",
    )
