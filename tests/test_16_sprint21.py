"""
Sprint 21 API checks:
- start simulated assessment
- wait for 1 evaluated question
- stop simulation
- finalize + report compose
- optional KG graph nodes
"""
import time
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=120)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:400]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def sprint21_simulation():
    suffix = uuid.uuid4().hex[:6]
    started = post("/assessments/simulated", {
        "client_name": "Migros-S21",
        "project_name": f"Sprint21-{suffix}",
        "company_profile": {"industry": "perakende", "size": "buyuk"},
        "max_workstreams": 1,
        "max_questions_per_workstream": 1,
    })
    assessment_id = started["id"]
    assert started["assessment_mode"] == "simulated"

    deadline = time.time() + 120
    evaluated = 0
    while time.time() < deadline:
        st = get(f"/assessments/{assessment_id}/simulation/status")
        progress = st.get("simulation_progress") or {}
        evaluated = progress.get("questions_evaluated", 0)
        if evaluated >= 1:
            break
        if st.get("simulation_status") in ("completed", "failed", "stopped"):
            break
        time.sleep(1)

    assert evaluated >= 1, "simulation should evaluate at least 1 question"

    stop = post(f"/assessments/{assessment_id}/simulation/stop", expected=200)
    assert stop["simulation_status"] == "stopped"

    final = post(f"/assessments/{assessment_id}/simulation/finalize", expected=200)
    assert final["report_id"]
    assert final["executive_summary"]
    assert final["ai_sections_updated"] >= 0

    report = get(f"/reports/{final['report_id']}")
    assert report.get("content_json")

    return {
        "assessment_id": assessment_id,
        "report_id": final["report_id"],
        "evaluated": evaluated,
    }


def test_start_simulated_assessment_fields(sprint21_simulation):
    data = get(f"/assessments/{sprint21_simulation['assessment_id']}")
    assert data["assessment_mode"] == "simulated"
    assert data["simulation_status"] in ("stopped", "finalized", "completed")


def test_simulation_status_endpoint(sprint21_simulation):
    st = get(f"/assessments/{sprint21_simulation['assessment_id']}/simulation/status")
    assert st["assessment_mode"] == "simulated"
    assert st["simulation_progress"]["questions_evaluated"] >= 1


def test_finalize_report_has_content(sprint21_simulation):
    report = get(f"/reports/{sprint21_simulation['report_id']}")
    assert report["executive_summary"]
    assert report["content_json"]


def test_kg_graph_after_simulation(sprint21_simulation):
    """KG nodes when Fuseki available; otherwise non-fatal empty graph."""
    try:
        graph = get(f"/knowledge/graph/assessment/{sprint21_simulation['assessment_id']}")
    except AssertionError:
        pytest.skip("Fuseki unavailable in this environment")
    nodes = graph.get("nodes", [])
    if not nodes:
        pytest.skip("No KG nodes (Fuseki may be offline)")
    types = {n.get("type", "").lower() for n in nodes}
    assert any("assessment" in t or "question" in t or "answer" in t for t in types)
