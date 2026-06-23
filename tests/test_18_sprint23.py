"""
Sprint 23 API checks:
- consultants CRUD + assessment assignment
- answer with consultant fields
- consultant synthesis
- AI maturity suggest
- question bank delete
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
def sprint23_ctx():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S23",
        "project_name": f"Sprint23-{suffix}",
    })
    consultant = post("/consultants", {
        "first_name": "Ayşe",
        "last_name": "Yılmaz",
        "role": "Architect",
        "expertise": ["LLM", "Kafka"],
    })
    post(f"/assessments/{assessment['id']}/consultants", {
        "consultant_id": consultant["id"],
    }, expected=201)
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S23",
        "status": "in_progress",
    })
    interview = post("/interviews", {
        "task_id": task["id"],
        "interviewee_name": "Ops Lead",
    })
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Cluster kaç node?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "12 node HA cluster.",
        "consultant_id": consultant["id"],
        "consultant_comment": "Mimari sağlam, DR eksik.",
    })
    return {
        "assessment_id": assessment["id"],
        "consultant_id": consultant["id"],
        "task_id": task["id"],
        "interview_id": interview["id"],
        "question_id": question["id"],
        "answer_id": answer["id"],
    }


def test_consultants_crud():
    c = post("/consultants", {
        "first_name": "Mehmet",
        "last_name": "Kaya",
        "role": "Lead",
    })
    got = get(f"/consultants/{c['id']}")
    assert got["first_name"] == "Mehmet"
    all_c = get("/consultants")
    assert any(x["id"] == c["id"] for x in all_c)
    delete(f"/consultants/{c['id']}")


def test_list_assessment_consultants(sprint23_ctx):
    consultants = get(f"/assessments/{sprint23_ctx['assessment_id']}/consultants")
    assert len(consultants) >= 1
    assert consultants[0]["first_name"] == "Ayşe"


def test_answer_consultant_fields(sprint23_ctx):
    answers = get(f"/interviews/questions/{sprint23_ctx['question_id']}/answers")
    assert len(answers) == 1
    assert answers[0]["consultant_id"] == sprint23_ctx["consultant_id"]
    assert "DR eksik" in (answers[0].get("consultant_comment") or "")


def test_consultant_synthesis(sprint23_ctx):
    # evaluate answer first so synthesis has content
    requests.post(
        api(f"/interviews/answers/{sprint23_ctx['answer_id']}/evaluate"),
        timeout=90,
    )
    data = post(
        f"/assessments/{sprint23_ctx['assessment_id']}/consultant-synthesis",
        expected=200,
    )
    assert data["consultant_synthesis"]
    assessment = get(f"/assessments/{sprint23_ctx['assessment_id']}")
    assert assessment.get("consultant_synthesis")


def test_ai_maturity_suggest(sprint23_ctx):
    data = post(
        f"/assessments/{sprint23_ctx['assessment_id']}/maturity/kubernetes/ai-suggest",
        expected=200,
    )
    assert 0 <= data["score"] <= 5
    assert data["maturity_level"]
    assert data["notes"]
    scores = get(f"/assessments/{sprint23_ctx['assessment_id']}/maturity")
    assert any(s["workstream"] == "kubernetes" for s in scores)


def test_finding_with_evidence(sprint23_ctx):
    ev = post("/evidences", {
        "interview_id": sprint23_ctx["interview_id"],
        "source": "interview",
        "content": "DR planı dokümante değil.",
        "evidence_type": "interview",
    })
    finding = post("/findings", {
        "task_id": sprint23_ctx["task_id"],
        "evidence_id": ev["id"],
        "description": "DR dokümantasyonu eksik",
        "severity": "medium",
        "confidence": 0.85,
    })
    assert finding["id"]


def test_question_bank_delete():
    suffix = uuid.uuid4().hex[:6]
    q = post("/question-bank", {
        "workstream": "kubernetes",
        "area": "general",
        "text": f"S23 delete test {suffix}",
        "order": 999,
        "is_active": True,
    })
    delete(f"/question-bank/{q['id']}")
    r = requests.get(api(f"/question-bank/{q['id']}"), timeout=30)
    assert r.status_code == 404
