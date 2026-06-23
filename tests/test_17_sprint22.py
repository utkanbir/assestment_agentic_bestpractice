"""
Sprint 22 API checks:
- assessment duplicate (metadata + optional tasks/Q&A)
- latest interview endpoint
- executive summary generation without findings (Q&A + maturity)
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


def delete(path, expected=204):
    r = requests.delete(api(path), timeout=30)
    assert r.status_code == expected, f"DELETE {path} -> {r.status_code}: {r.text[:300]}"


@pytest.fixture(scope="module")
def sprint22_source():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S22",
        "project_name": f"Sprint22-{suffix}",
        "description": "Sprint22 duplicate source",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S22 test",
        "status": "in_progress",
    })
    interview = post("/interviews", {
        "task_id": task["id"],
        "interviewee_name": "Test User",
        "interviewee_role": "Architect",
    })
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Kubernetes cluster kaç node?",
        "order": 1,
        "agent_suggested": False,
    })
    post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "12 node production cluster.",
    })
    return {
        "assessment_id": assessment["id"],
        "task_id": task["id"],
        "interview_id": interview["id"],
        "question_id": question["id"],
    }


def test_duplicate_assessment_metadata_only(sprint22_source):
    dup = post(f"/assessments/{sprint22_source['assessment_id']}/duplicate", {
        "include_qa": False,
        "include_tasks": False,
    })
    assert dup["id"] != sprint22_source["assessment_id"]
    assert "Copy" in dup["project_name"]
    assert dup["client_name"] == "Migros-S22"
    assert dup["description"] == "Sprint22 duplicate source"
    tasks = get("/tasks", params={"assessment_id": dup["id"]})
    assert tasks == []


def test_duplicate_assessment_with_qa(sprint22_source):
    dup = post(f"/assessments/{sprint22_source['assessment_id']}/duplicate", {
        "include_qa": True,
        "include_tasks": True,
    })
    tasks = get("/tasks", params={"assessment_id": dup["id"]})
    assert len(tasks) == 1
    assert tasks[0]["workstream"] == "kubernetes"

    interviews = get("/interviews", params={"task_id": tasks[0]["id"]})
    assert len(interviews) == 1
    questions = get(f"/interviews/{interviews[0]['id']}/questions")
    assert len(questions) == 1
    assert "Kubernetes" in questions[0]["text"]
    answers = get(f"/interviews/questions/{questions[0]['id']}/answers")
    assert len(answers) == 1
    assert "12 node" in answers[0]["text"]


def test_latest_interview(sprint22_source):
    latest = get(f"/assessments/{sprint22_source['assessment_id']}/interviews/latest")
    assert latest["interview_id"] == sprint22_source["interview_id"]
    assert latest["workstream"] == "kubernetes"
    assert latest["task_id"] == sprint22_source["task_id"]


def test_latest_interview_not_found():
    suffix = uuid.uuid4().hex[:6]
    empty = post("/assessments", {
        "client_name": "Empty-S22",
        "project_name": f"NoIv-{suffix}",
    })
    r = requests.get(api(f"/assessments/{empty['id']}/interviews/latest"), timeout=30)
    assert r.status_code == 404


def test_generate_summary_without_findings(sprint22_source):
    """No findings — should succeed using Q&A summary path (not 422)."""
    data = post(
        f"/orchestrator/{sprint22_source['assessment_id']}/generate-summary",
        expected=200,
    )
    assert data["summary"]
    assert data["assessment_id"] == sprint22_source["assessment_id"]
    assert data["total_risks"] == 0


def test_delete_assessment(sprint22_source):
    suffix = uuid.uuid4().hex[:6]
    temp = post("/assessments", {
        "client_name": "Delete-S22",
        "project_name": f"Del-{suffix}",
    })
    delete(f"/assessments/{temp['id']}")
    r = requests.get(api(f"/assessments/{temp['id']}"), timeout=30)
    assert r.status_code == 404
