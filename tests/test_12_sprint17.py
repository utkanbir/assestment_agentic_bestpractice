"""
Sprint 17 API checks:
- enriched executive summary
- pending-questions
- heatmap findings drill-down
- roadmap generate
- approval filter fix
"""
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=90)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def sprint17_setup():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S17",
        "project_name": f"Sprint17-{suffix}",
        "description": "Sprint17 integration test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S17 test",
        "status": "in_progress",
    })
    return {"assessment_id": assessment["id"], "task_id": task["id"]}


def test_executive_summary_enriched_fields(sprint17_setup):
    data = get(f"/orchestrator/{sprint17_setup['assessment_id']}/executive-summary")
    assert "workstream_summaries" in data
    assert "top_risks" in data
    assert "top_recommendations" in data
    assert "avg_maturity" in data
    assert "pending_approvals" in data
    assert "tasks_total" in data


def test_pending_questions_endpoint(sprint17_setup):
    data = get(
        "/approvals/pending-questions",
        params={"assessment_id": sprint17_setup["assessment_id"]},
    )
    assert isinstance(data, list)


def test_approvals_pending_scoped_to_assessment(sprint17_setup):
    data = get(
        "/approvals/pending",
        params={"assessment_id": sprint17_setup["assessment_id"]},
    )
    assert "total" in data
    assert "pending_findings" in data


def test_roadmap_and_generate(sprint17_setup):
    items = get(f"/orchestrator/{sprint17_setup['assessment_id']}/roadmap")
    assert isinstance(items, list)
    generated = post(
        f"/orchestrator/{sprint17_setup['assessment_id']}/generate-roadmap",
        expected=200,
    )
    assert isinstance(generated, list)


def test_heatmap_findings_drilldown(sprint17_setup):
    heatmap = get(f"/orchestrator/{sprint17_setup['assessment_id']}/risk-heatmap")
    if not heatmap:
        pytest.skip("no heatmap cells")
    cell = heatmap[0]
    findings = get(
        f"/orchestrator/{sprint17_setup['assessment_id']}/risk-heatmap/findings",
        params={
            "capability_area": cell["capability_area"],
            "severity": cell["severity"],
        },
    )
    assert isinstance(findings, list)


def test_maturity_target_score_field(sprint17_setup):
    aid = sprint17_setup["assessment_id"]
    put = requests.put(
        api(f"/assessments/{aid}/maturity/kubernetes"),
        json={"score": 2.5, "maturity_level": "developing", "target_score": 4.0},
        timeout=30,
    )
    assert put.status_code == 200, put.text[:300]
    body = put.json()
    assert body.get("target_score") == 4.0
