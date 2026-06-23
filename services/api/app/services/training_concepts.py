"""Domain concept catalog and resolution for training enrichment (refersToConcept)."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_DATA_NS = "https://aakp.ai/data"


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    path = Path(__file__).parent.parent / "data" / "training_concepts.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def concept_uri(slug: str) -> str:
    return f"{_DATA_NS}/{slug}"


def list_concepts_for_workstream(workstream: str) -> list[dict]:
    """Candidate concepts: workstream capabilities + all practice themes."""
    cat = _load_catalog()
    caps = cat.get("workstream_capabilities", {}).get(workstream, [])
    cap_defs = cat.get("capabilities", {})
    theme_defs = cat.get("themes", {})

    out: list[dict] = []
    seen: set[str] = set()
    for slug in caps:
        if slug in seen:
            continue
        seen.add(slug)
        meta = cap_defs.get(slug, {})
        out.append({
            "id": slug,
            "uri": concept_uri(slug),
            "label": meta.get("label", slug),
            "description": meta.get("description", ""),
            "kind": "capability",
        })
    for slug, meta in theme_defs.items():
        if slug in seen:
            continue
        seen.add(slug)
        out.append({
            "id": slug,
            "uri": concept_uri(slug),
            "label": meta.get("label", slug),
            "description": ", ".join(meta.get("keywords", [])),
            "kind": "theme",
        })
    return out


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def keyword_fallback_concept_ids(
    workstream: str,
    question_text: str,
    answer_text: str,
    *,
    max_concepts: int = 3,
) -> list[str]:
    """Pick concepts without LLM — keywords + default workstream capability."""
    combined = _normalize(f"{question_text} {answer_text}")
    cat = _load_catalog()
    selected: list[str] = []

    for slug in cat.get("workstream_capabilities", {}).get(workstream, [])[:1]:
        selected.append(slug)

    for slug, meta in cat.get("themes", {}).items():
        for kw in meta.get("keywords", []):
            if kw.lower() in combined:
                selected.append(slug)
                break

    # dedupe preserve order
    out: list[str] = []
    for s in selected:
        if s not in out:
            out.append(s)
    return out[:max_concepts]


def resolve_concept_uris(concept_ids: list[str]) -> list[str]:
    cat = _load_catalog()
    all_ids: set[str] = set(cat.get("capabilities", {}).keys())
    all_ids.update(cat.get("themes", {}).keys())

    uris: list[str] = []
    for cid in concept_ids:
        if cid not in all_ids:
            continue
        uri = concept_uri(cid)
        if uri not in uris:
            uris.append(uri)
    return uris


def resolve_concepts_for_training(
    workstream: str,
    question_text: str,
    answer_text: str,
    llm_ids: list[str] | None = None,
    *,
    max_concepts: int = 3,
) -> list[str]:
    if llm_ids:
        uris = resolve_concept_uris(llm_ids[:max_concepts])
        if uris:
            return uris
    ids = keyword_fallback_concept_ids(
        workstream, question_text, answer_text, max_concepts=max_concepts,
    )
    return resolve_concept_uris(ids)
