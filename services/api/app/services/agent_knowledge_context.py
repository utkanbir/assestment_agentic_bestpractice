"""Build KG layer context (schema + agent training instances) for LLM prompts."""
from app.services.sparql_client import sparql_client


async def build_kg_context(
    workstream: str,
    *,
    training_limit: int = 6,
    schema_limit: int = 4,
) -> tuple[str, int, int]:
    """Return (combined KG context text, training_hits, schema_hits)."""
    training_bindings: list[dict] = []
    schema_bindings: list[dict] = []
    try:
        training_bindings = await sparql_client.get_agent_training_context(
            workstream, limit=training_limit,
        )
    except Exception:
        pass
    try:
        schema_bindings = await sparql_client.get_ontology_context(
            workstream, limit=schema_limit,
        )
    except Exception:
        pass

    parts: list[str] = []
    training_text = sparql_client.format_agent_training_context(training_bindings)
    if training_text:
        parts.append(training_text)
    if schema_bindings:
        schema_lines = ["Ontoloji şeması (ilgili sınıflar):"]
        for row in schema_bindings:
            label = row.get("label", {}).get("value") or row.get("class", {}).get("value", "")
            comment = row.get("comment", {}).get("value", "")
            schema_lines.append(f"- {label}: {comment}".strip(": "))
        parts.append("\n".join(schema_lines))

    return "\n\n".join(parts), len(training_bindings), len(schema_bindings)
