# S5-BA-001: Input guardrail middleware — Presidio PII tarama
# S5-BA-002/003: Output validator — evidence chain + PII filter

import json
import logging

import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

log = logging.getLogger("guardrails")

# Routes that carry user-generated text → scan for PII
_PII_SCAN_PATHS = {
    "/api/v1/answers",
    "/api/v1/evidences",
    "/api/v1/findings",
}

# Fields in request body that may contain sensitive text
_TEXT_FIELDS = ("text", "content", "description", "raw_transcript")


async def _presidio_analyze(text: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                f"{settings.presidio_analyzer_url}/analyze",
                json={"text": text, "language": "tr",
                      "entities": ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
                                   "CREDIT_CARD", "IBAN_CODE", "NRP",
                                   "TR_TC_KimlikNo", "TR_IBAN"]},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return []


class PIIGuardrailMiddleware(BaseHTTPMiddleware):
    """S5-BA-001: Scan incoming request bodies for PII before processing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            path = request.url.path.rstrip("/")
            if any(path.startswith(p) for p in _PII_SCAN_PATHS):
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = json.loads(body_bytes)
                        for field in _TEXT_FIELDS:
                            text = body.get(field, "")
                            if text and len(text) > 10:
                                entities = await _presidio_analyze(text)
                                high_conf = [e for e in entities if e.get("score", 0) >= 0.85]
                                if high_conf:
                                    entity_types = list({e["entity_type"] for e in high_conf})
                                    log.warning(
                                        "PII detected in %s.%s: %s (path=%s)",
                                        request.method, field, entity_types, path
                                    )
                                    # Block only CRITICAL PII (TC kimlik, IBAN, credit card)
                                    critical = {"TR_TC_KimlikNo", "IBAN_CODE", "CREDIT_CARD"}
                                    if critical & set(entity_types):
                                        return JSONResponse(
                                            status_code=422,
                                            content={
                                                "detail": f"PII detected in field '{field}': "
                                                          f"{entity_types}. Remove sensitive data before submitting."
                                            },
                                        )
                except Exception:
                    pass  # PII check failure is non-fatal — do not block request

        return await call_next(request)
