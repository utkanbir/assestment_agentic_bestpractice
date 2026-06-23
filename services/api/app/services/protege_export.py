"""Merge ontology TBox + Fuseki agent subgraph into one Protege-ready Turtle file."""
from __future__ import annotations

from pathlib import Path

from rdflib import Graph, OWL

from app.services.sparql_client import _workstream_agent_uri, sparql_client


def _ontology_dir() -> Path:
    bundled = Path(__file__).resolve().parent.parent / "data" / "ontology"
    if bundled.is_dir():
        return bundled
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "knowledge" / "ontology"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("ontology directory not found")


def strip_owl_imports(graph: Graph) -> None:
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)


def load_ontology_graph(*, include_instances: bool = False) -> Graph:
    graph = Graph()
    for ttl in sorted(_ontology_dir().glob("*.ttl")):
        if not include_instances and ttl.name.endswith("_instances.ttl"):
            continue
        try:
            graph.parse(ttl, format="turtle")
        except Exception:
            continue
    strip_owl_imports(graph)
    return graph


def _agent_construct_query(workstream: str) -> str:
    agent_uri = _workstream_agent_uri(workstream)
    ws_lit = workstream.replace("\\", "\\\\").replace('"', '\\"')
    return f"""
CONSTRUCT {{ ?s ?p ?o }}
WHERE {{
  {{
    GRAPH <https://aakp.ai/graph/agents> {{
      ?reg a aakp:AssessmentAgent ; aakp:hasWorkstream "{ws_lit}" .
      ?reg ?p ?o .
      BIND(?reg AS ?s)
    }}
  }}
  UNION
  {{
    GRAPH <https://aakp.ai/graph/assessment> {{
      VALUES ?agent {{ <{agent_uri}> }}
      {{
        ?agent ?p ?o .
        BIND(?agent AS ?s)
      }}
      UNION
      {{
        ?agent (aakp:hasTrainingEvent|aakp:hasAgentKnowledge) ?event .
        ?event ?p ?o .
        BIND(?event AS ?s)
      }}
      UNION
      {{
        ?agent (aakp:hasTrainingEvent|aakp:hasAgentKnowledge) ?event .
        ?event aakp:refersToConcept ?concept .
        ?concept ?p ?o .
        BIND(?concept AS ?s)
      }}
    }}
  }}
}}
"""


async def build_agent_protege_bundle(workstream: str) -> tuple[str, int]:
    graph = load_ontology_graph(include_instances=False)
    tbox_count = len(graph)

    instance_count = 0
    try:
        turtle = await sparql_client.construct(_agent_construct_query(workstream))
        if turtle.strip():
            subgraph = Graph()
            subgraph.parse(data=turtle, format="turtle")
            instance_count = len(subgraph)
            graph += subgraph
    except Exception:
        pass

    body = graph.serialize(format="turtle")
    return body, tbox_count + instance_count


def _full_kg_construct_query() -> str:
    return """
CONSTRUCT { ?s ?p ?o }
WHERE {
  {
    GRAPH <https://aakp.ai/graph/agents> { ?s ?p ?o }
  }
  UNION
  {
    GRAPH <https://aakp.ai/graph/assessment> { ?s ?p ?o }
  }
}
"""


async def build_full_kg_protege_bundle() -> tuple[str, int]:
    """TBox + all agent registry + all KM instance triples for Protege."""
    graph = load_ontology_graph(include_instances=False)
    tbox_count = len(graph)

    instance_count = 0
    try:
        turtle = await sparql_client.construct(_full_kg_construct_query())
        if turtle.strip():
            subgraph = Graph()
            subgraph.parse(data=turtle, format="turtle")
            instance_count = len(subgraph)
            graph += subgraph
    except Exception:
        pass

    body = graph.serialize(format="turtle")
    return body, tbox_count + instance_count
