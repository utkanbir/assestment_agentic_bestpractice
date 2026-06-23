"""Load consultant expertise catalog from YAML."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class ExpertiseGroupOut(BaseModel):
    id: str
    name: str
    tags: list[str]


class ExpertiseCatalogOut(BaseModel):
    groups: list[ExpertiseGroupOut]


def _resolve_catalog_path() -> Path:
    bundled = Path(__file__).resolve().parent.parent / "data" / "expertise_catalog.yaml"
    if bundled.is_file():
        return bundled
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "knowledge" / "consultants" / "expertise_catalog.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("expertise_catalog.yaml not found")


@lru_cache
def get_expertise_catalog() -> ExpertiseCatalogOut:
    path = _resolve_catalog_path()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    groups = [ExpertiseGroupOut(**g) for g in data.get("groups", [])]
    return ExpertiseCatalogOut(groups=groups)


def all_valid_tags() -> set[str]:
    return {tag for g in get_expertise_catalog().groups for tag in g.tags}


def validate_expertise_tags(tags: list[str]) -> list[str]:
    if not tags:
        return []
    valid = all_valid_tags()
    invalid = [t for t in tags if t not in valid]
    if invalid:
        raise ValueError(f"Unknown expertise tags: {', '.join(invalid)}")
    return list(dict.fromkeys(tags))
