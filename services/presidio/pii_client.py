# S5-SA-007/008 + S5-BA-001/003: Presidio PII detection/anonymization client
import httpx
from app.core.config import settings

_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
             "IBAN_CODE", "IP_ADDRESS", "NRP", "LOCATION",
             "TR_TC_KimlikNo", "TR_IBAN"]


async def analyze(text: str, language: str = "tr") -> list[dict]:
    """Return list of detected PII entities with score and position."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.presidio_analyzer_url}/analyze",
                json={"text": text, "language": language, "entities": _ENTITIES},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return []


async def anonymize(text: str, language: str = "tr") -> str:
    """Replace PII with <ENTITY_TYPE> placeholders. Returns anonymized text."""
    entities = await analyze(text, language)
    if not entities:
        return text
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.presidio_anonymizer_url}/anonymize",
                json={
                    "text": text,
                    "analyzer_results": entities,
                    "anonymizers": {"DEFAULT": {"type": "replace", "new_value": "<PII>"}},
                },
            )
            resp.raise_for_status()
            return resp.json().get("text", text)
    except Exception:
        return text


def has_pii(entities: list[dict], threshold: float = 0.7) -> bool:
    return any(e.get("score", 0) >= threshold for e in entities)
