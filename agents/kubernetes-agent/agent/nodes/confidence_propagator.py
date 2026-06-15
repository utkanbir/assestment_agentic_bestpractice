"""
S2-AA-002: Confidence propagation node.

Triggers all materialized inference rules via the API:
  Rule 01 — Finding → Gap auto-link (approved, conf >= 0.7, category match)
  Rule 05 — Gap.inferredConfidence = MAX(finding.confidence) per gap
  Rule 07 — Finding.isInvalid = true when no supportedByEvidence

After rules run, fetches Gap confidence scores and decides whether
overall evidence quality is sufficient, or flags low-confidence gaps
for the report.
"""
import logging

import httpx

from agent.config import settings
from agent.state import KubernetesAgentState

logger = logging.getLogger(__name__)

_LOW_CONFIDENCE_THRESHOLD = 0.6


async def confidence_propagator(state: KubernetesAgentState) -> dict:
    inference_results: dict[str, str] = {}
    gap_confidence: list[dict] = []
    low_confidence_gaps: list[dict] = []

    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=30
    ) as client:
        # Trigger all inference rules
        inf_resp = await client.post("/api/v1/knowledge/inference/run")
        if inf_resp.status_code == 200:
            data = inf_resp.json()
            inference_results = data.get("results", {})
            logger.info(
                "Inference rules completed: %d rules, results=%s",
                data.get("rules_run", 0), inference_results,
            )
        else:
            logger.warning(
                "Inference run failed: %s %s", inf_resp.status_code, inf_resp.text
            )

        # Fetch Gap confidence scores (populated by Rule 5)
        gc_resp = await client.get("/api/v1/knowledge/gaps/confidence")
        if gc_resp.status_code == 200:
            gap_confidence = gc_resp.json()

    # Identify gaps with low or missing confidence
    for binding in gap_confidence:
        conf_val = binding.get("inferredConfidence", {}).get("value")
        gap_title = binding.get("gapTitle", {}).get("value", "Unknown gap")
        cap_area = binding.get("capabilityArea", {}).get("value", "")

        if conf_val is None:
            low_confidence_gaps.append({
                "gap": binding.get("gap", {}).get("value", ""),
                "title": gap_title,
                "capability_area": cap_area,
                "inferred_confidence": None,
                "reason": "no approved finding linked yet",
            })
        elif float(conf_val) < _LOW_CONFIDENCE_THRESHOLD:
            low_confidence_gaps.append({
                "gap": binding.get("gap", {}).get("value", ""),
                "title": gap_title,
                "capability_area": cap_area,
                "inferred_confidence": float(conf_val),
                "reason": f"confidence {float(conf_val):.2f} below threshold {_LOW_CONFIDENCE_THRESHOLD}",
            })

    return {
        "inference_results": inference_results,
        "low_confidence_gaps": low_confidence_gaps,
    }
