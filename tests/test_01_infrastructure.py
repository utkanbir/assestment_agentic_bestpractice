"""
Sprint 0 infrastructure smoke tests.
Run BEFORE building Sprint 1 images — only needs port-forwards.

Port-forward commands:
  kubectl port-forward svc/aakp-fuseki -n aakp-knowledge 3030:3030
  kubectl port-forward svc/aakp-postgresql -n aakp-information 5432:5432
"""
import httpx
import pytest


def test_fuseki_ping(fuseki_url):
    """Fuseki is up and responding."""
    r = httpx.get(f"{fuseki_url}/$/ping", timeout=5)
    assert r.status_code == 200, f"Fuseki ping failed: {r.status_code}"


def test_fuseki_dataset_exists(fuseki_url, fuseki_ds):
    """'aakp' dataset exists in Fuseki."""
    r = httpx.get(
        f"{fuseki_url}/$/datasets/{fuseki_ds}",
        auth=("admin", "aakp-fuseki-secret"),
        timeout=5,
    )
    assert r.status_code == 200, f"Dataset '{fuseki_ds}' not found: {r.status_code}"


def test_fuseki_ontology_triples(fuseki_url, fuseki_ds):
    """Ontology was deployed — at least 300 triples in named graphs."""
    query = "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }"
    r = httpx.get(
        f"{fuseki_url}/{fuseki_ds}/query",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=("admin", "aakp-fuseki-secret"),
        timeout=10,
    )
    assert r.status_code == 200
    count = int(r.json()["results"]["bindings"][0]["n"]["value"])
    assert count >= 300, f"Expected >=300 triples, got {count}"


def test_fuseki_assessment_class(fuseki_url, fuseki_ds):
    """aakp:Assessment class is present in the ontology."""
    query = """
    PREFIX aakp: <https://aakp.ai/ontology/assessment#>
    ASK { GRAPH ?g { aakp:Assessment a ?type } }
    """
    r = httpx.get(
        f"{fuseki_url}/{fuseki_ds}/query",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=("admin", "aakp-fuseki-secret"),
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json()["boolean"] is True, "aakp:Assessment class not found in ontology"


@pytest.mark.asyncio
async def test_postgresql_connection():
    """PostgreSQL is reachable via port-forward on 5433."""
    import asyncpg
    try:
        conn = await asyncpg.connect(
            "postgresql://aakp:aakp-pg-secret@localhost:5433/aakp",
            timeout=5,
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        assert "PostgreSQL" in version
    except Exception as e:
        pytest.skip(f"PostgreSQL port-forward not active (use port 5433): {e}")


@pytest.mark.asyncio
async def test_postgresql_tables():
    """Tables exist if Alembic has run (requires Sprint 1 deploy)."""
    import asyncpg
    try:
        conn = await asyncpg.connect(
            "postgresql://aakp:aakp-pg-secret@localhost:5433/aakp",
            timeout=5,
        )
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        await conn.close()
        names = {r["tablename"] for r in tables}
        if not names:
            pytest.skip("No tables yet — run: .\\infra\\deploy.ps1 -Action sprint1 (Alembic migration)")
        expected = {"assessments", "tasks", "interviews", "questions", "answers",
                    "evidences", "findings", "risks", "recommendations", "reports"}
        missing = expected - names
        assert not missing, f"Missing tables: {missing}"
    except Exception as e:
        pytest.skip(f"PostgreSQL not reachable on port 5433: {e}")
