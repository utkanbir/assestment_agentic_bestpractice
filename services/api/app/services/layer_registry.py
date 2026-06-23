"""Load 4-layer architecture registry from layers.yaml."""

import os
from functools import lru_cache
from pathlib import Path

import yaml

from app.schemas.architecture import LayerOut, LayersRegistryOut, TechnologyOut


def _resolve_registry_path() -> Path:
    bundled = Path(__file__).resolve().parent.parent / "data" / "layers.yaml"
    if bundled.is_file():
        return bundled
    # Local dev: repo root knowledge/architecture/layers.yaml
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "knowledge" / "architecture" / "layers.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("layers.yaml registry not found")


def _qdrant_console_url() -> str:
    explicit = os.environ.get("QDRANT_CONSOLE_URL", "").strip()
    if explicit:
        return explicit
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = os.environ.get("QDRANT_HTTP_PORT", "6333")
    return f"http://{host}:{port}/dashboard"


def _apply_env_overrides(tech: TechnologyOut) -> TechnologyOut:
    if tech.id == "qdrant":
        return tech.model_copy(update={"console_url": _qdrant_console_url()})
    return tech


@lru_cache
def get_layers_registry() -> LayersRegistryOut:
    path = _resolve_registry_path()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    layers = []
    for layer in data["layers"]:
        technologies = [
            _apply_env_overrides(TechnologyOut(**tech)) for tech in layer["technologies"]
        ]
        layers.append(
            LayerOut(
                id=layer["id"],
                name=layer["name"],
                description=layer["description"],
                namespace=layer["namespace"],
                technologies=technologies,
            )
        )
    return LayersRegistryOut(layers=layers)
