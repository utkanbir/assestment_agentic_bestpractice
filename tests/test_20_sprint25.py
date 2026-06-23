"""
Sprint 25 API smoke tests:
- GET /architecture/layers
- GET /knowledge/graph/assessment/{id}
- POST /orchestrator/{id}/generate-recommendations
- GET /health/db
"""
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=90)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:400]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def patch(path, json, expected=200):
    r = requests.patch(api(path), json=json, timeout=30)
    assert r.status_code == expected, f"PATCH {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def sprint25_assessment():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S25",
        "project_name": f"Sprint25-{suffix}",
        "description": "Sprint 25 smoke test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S25 test",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "S25Tester"})
    evidence = post("/evidences", {
        "interview_id": interview["id"],
        "source": "s25-test",
        "content": "Cluster autoscaler eksik, node pool kapasitesi yetersiz.",
        "evidence_type": "interview",
    })
    finding = post("/findings", {
        "task_id": task["id"],
        "evidence_id": evidence["id"],
        "description": "Kubernetes kapasite planlaması eksik",
        "severity": "high",
        "confidence": 0.85,
    })
    patch(f"/approvals/findings/{finding['id']}", {"decision": "approved", "reviewer_note": "s25"})
    yield {"assessment_id": assessment["id"], "finding_id": finding["id"]}


def test_health_db():
    base = API_BASE.rsplit("/api/v1", 1)[0]
    r = requests.get(f"{base}/health/db", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert body.get("db") == "connected"


def test_architecture_layers():
    data = get("/architecture/layers")
    assert "layers" in data
    assert len(data["layers"]) >= 4
    layer_ids = {layer["id"] for layer in data["layers"]}
    assert {"data", "information", "knowledge", "agent"}.issubset(layer_ids)
    pg = next(
        t for layer in data["layers"] for t in layer["technologies"] if t["id"] == "postgresql"
    )
    assert pg["active_in_api"] is True


def test_knowledge_graph_assessment(sprint25_assessment):
    aid = sprint25_assessment["assessment_id"]
    graph = get(f"/knowledge/graph/assessment/{aid}")
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_generate_recommendations(sprint25_assessment):
    aid = sprint25_assessment["assessment_id"]
    result = post(f"/orchestrator/{aid}/generate-recommendations", expected=200)
    assert "created" in result
    assert result["created"] >= 1
    assert len(result["recommendations"]) >= 1
    rec = result["recommendations"][0]
    assert rec["finding_id"] == sprint25_assessment["finding_id"]
    assert rec["description"]
