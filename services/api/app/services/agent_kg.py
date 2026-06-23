"""Agent-scoped Knowledge Graph read model (Fuseki SPARQL)."""
from __future__ import annotations

from app.services.sparql_client import _workstream_agent_uri, sparql_client

def short_uri(uri: str) -> str:
    if not uri:
        return ""
    if uri.startswith('"'):
        return uri[:80]
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def node_type_for_uri(uri: str) -> str:
    if "/agent/" in uri:
        return "agent"
    if "/training/" in uri:
        return "learning_event"
    if "/agent-knowledge/" in uri:
        return "knowledge"
    if "/capability/" in uri or "/theme/" in uri:
        return "concept"
    if "/ontology/" in uri or uri.endswith("TrainingInteraction") or uri.endswith("AgentKnowledge"):
        return "ontology"
    return "resource"


def predicate_short(predicate: str) -> str:
    if "#" in predicate:
        return predicate.split("#")[-1]
    return predicate.rstrip("/").split("/")[-1]


def agent_kg_sparql_query(workstream: str) -> str:
    agent_uri = _workstream_agent_uri(workstream)
    return f"""PREFIX aakp: <https://aakp.ai/ontology/assessment#>
PREFIX arch: <https://aakp.ai/ontology/architecture#>

SELECT ?subject ?predicate ?object ?objectLabel
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    VALUES ?agent {{ <{agent_uri}> }}
    {{
      ?agent ?predicate ?object .
      BIND(?agent AS ?subject)
    }}
    UNION
    {{
      ?agent (aakp:hasTrainingEvent|aakp:hasAgentKnowledge) ?event .
      ?event ?predicate ?object .
      BIND(?event AS ?subject)
    }}
    UNION
    {{
      ?agent (aakp:hasTrainingEvent|aakp:hasAgentKnowledge) ?event .
      ?event aakp:refersToConcept ?concept .
      ?concept ?predicate ?object .
      BIND(?concept AS ?subject)
    }}
    OPTIONAL {{ ?object arch:hasName ?objectLabel }}
  }}
}}
ORDER BY ?subject ?predicate
"""


async def fetch_agent_kg_triples(workstream: str) -> list[dict]:    result = await sparql_client.query(agent_kg_sparql_query(workstream))
    rows: list[dict] = []
    for b in result.get("results", {}).get("bindings", []):
        obj = b.get("object", {})
        obj_val = obj.get("value", "")
        obj_type = obj.get("type", "literal")
        obj_label = (b.get("objectLabel") or {}).get("value")
        is_literal = obj_type != "uri"
        if is_literal and not obj_label:
            obj_label = obj_val[:120]
        rows.append({
            "subject": b.get("subject", {}).get("value", ""),
            "predicate": b.get("predicate", {}).get("value", ""),
            "object": obj_val,
            "object_label": obj_label,
            "object_is_literal": is_literal,
        })
    return rows


def triples_to_graph(triples: list[dict]) -> dict:
    """Build nodes/edges for visualization from SPARQL triple rows."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    edge_keys: set[str] = set()

    def ensure_node(uri: str) -> None:
        if uri not in nodes:
            nodes[uri] = {
                "id": uri,
                "label": short_uri(uri),
                "type": node_type_for_uri(uri),
            }

    for i, row in enumerate(triples):
        subj = row["subject"]
        pred = row["predicate"]
        obj = row["object"]
        if not subj:
            continue
        ensure_node(subj)
        pred_label = predicate_short(pred)
        if row.get("object_is_literal"):
            lit_id = f"lit:{subj}:{i}"
            lit_label = (row.get("object_label") or obj)[:60]
            nodes[lit_id] = {"id": lit_id, "label": lit_label, "type": "literal"}
            ek = f"{subj}|{pred_label}|{lit_id}"
            if ek not in edge_keys:
                edge_keys.add(ek)
                edges.append({"source": subj, "target": lit_id, "label": pred_label})
        elif obj.startswith("http"):
            ensure_node(obj)
            label = row.get("object_label")
            if label:
                nodes[obj]["label"] = label
            ek = f"{subj}|{pred_label}|{obj}"
            if ek not in edge_keys:
                edge_keys.add(ek)
                edges.append({"source": subj, "target": obj, "label": pred_label})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }
