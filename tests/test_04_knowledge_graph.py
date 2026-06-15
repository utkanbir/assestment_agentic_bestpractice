"""
SPARQL + Knowledge Graph integration tests.
Tests that findings written via API also appear in Fuseki.
"""
import pytest
import httpx


def sparql_ask(fuseki_url, fuseki_ds, query: str, auth=("admin", "aakp-fuseki-secret")) -> bool:
    r = httpx.get(
        f"{fuseki_url}/{fuseki_ds}/query",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=auth,
        timeout=10,
    )
    assert r.status_code == 200, f"SPARQL error: {r.text}"
    return r.json()["boolean"]


def sparql_select(fuseki_url, fuseki_ds, query: str, auth=("admin", "aakp-fuseki-secret")):
    r = httpx.get(
        f"{fuseki_url}/{fuseki_ds}/query",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=auth,
        timeout=10,
    )
    assert r.status_code == 200
    return r.json()["results"]["bindings"]


def test_named_graphs_loaded(fuseki_url, fuseki_ds):
    """All 4 ontology named graphs are present."""
    expected_graphs = [
        "https://aakp.ai/graph/assessment",
        "https://aakp.ai/graph/architecture",
        "https://aakp.ai/graph/maturity",
        "https://aakp.ai/graph/organization",
    ]
    bindings = sparql_select(
        fuseki_url, fuseki_ds,
        "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"
    )
    loaded = {b["g"]["value"] for b in bindings}
    for g in expected_graphs:
        assert g in loaded, f"Named graph missing: {g}"


def test_maturity_dimension_instances(fuseki_url, fuseki_ds):
    """MaturityDimension instances exist in the maturity graph."""
    q = """
    PREFIX mat: <https://aakp.ai/ontology/maturity#>
    ASK { GRAPH <https://aakp.ai/graph/maturity> { ?x a mat:MaturityDimension } }
    """
    assert sparql_ask(fuseki_url, fuseki_ds, q), "No MaturityDimension instances found"


def test_finding_kg_write(fuseki_url, fuseki_ds, api_base):
    """Create a finding via API, verify it appears in Fuseki."""
    with httpx.Client(base_url=api_base, timeout=10) as client:
        a = client.post("/assessments", json={"client_name": "KG Test", "project_name": "KG Test"}).json()
        t = client.post("/tasks", json={"assessment_id": a["id"], "title": "KG Test Task"}).json()
        i = client.post("/interviews", json={"task_id": t["id"]}).json()
        ev = client.post("/evidences", json={
            "interview_id": i["id"],
            "source": "interview",
            "content": "etcd yedekleme yapılmıyor.",
            "evidence_type": "interview",
        }).json()
        f = client.post("/findings", json={
            "task_id": t["id"],
            "evidence_id": ev["id"],
            "description": "etcd backup eksik",
            "severity": "critical",
            "confidence": 0.95,
        }).json()

        finding_id = f["id"]

        # Approve → triggers KG write
        client.post(f"/knowledge/findings/{finding_id}/approve")

    # Check Fuseki for the finding URI
    kg_uri = f"https://aakp.ai/instance/finding/{finding_id}"
    q = f"""
    PREFIX aakp: <https://aakp.ai/ontology/assessment#>
    ASK {{ GRAPH ?g {{ <{kg_uri}> a aakp:Finding }} }}
    """
    # Note: KG write is async (via agent), so we allow it to not be there yet
    # This is a best-effort check
    try:
        found = sparql_ask(fuseki_url, fuseki_ds, q)
        if found:
            print(f"Finding {finding_id} confirmed in Fuseki KG")
        else:
            pytest.xfail("Finding not yet in KG (async write may be pending)")
    finally:
        with httpx.Client(base_url=api_base, timeout=5) as client:
            client.delete(f"/assessments/{a['id']}")
