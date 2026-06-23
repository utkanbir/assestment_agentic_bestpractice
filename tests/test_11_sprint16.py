"""
Sprint 16 API checks:
- assessment context related routes
- ontology schema route
- execution transactions route
- standalone chat route
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
def sprint16_setup():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S16",
        "project_name": f"Sprint16-{suffix}",
        "description": "Sprint16 integration test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S16 test",
        "status": "in_progress",
    })
    interview = post("/interviews", {
        "task_id": task["id"],
        "interviewee_name": "Sprint16 Tester",
    })
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "S16 icin soru",
        "order": 1,
        "agent_suggested": False,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "S16 cevabi",
    })
    return {
        "assessment_id": assessment["id"],
        "interview_id": interview["id"],
        "question_id": question["id"],
        "answer_id": answer["id"],
        "answer_txn": answer.get("transaction_id"),
    }


def test_ontology_schema_parses_ttl():
    data = get("/knowledge/ontology/schema")
    assert "classes" in data and "properties" in data
    assert len(data["classes"]) >= 10
    assert isinstance(data["sources"], list) and len(data["sources"]) >= 1


def test_evaluate_returns_transaction_and_knowledge_touch(sprint16_setup):
    result = post(f"/interviews/answers/{sprint16_setup['answer_id']}/evaluate", expected=200)
    assert result.get("transaction_id")
    layers = {t["layer"] for t in result.get("layer_trace", [])}
    assert "knowledge" in layers


def test_transactions_list_and_detail(sprint16_setup):
    txs = get("/architecture/transactions", {"assessment_id": sprint16_setup["assessment_id"]})
    assert isinstance(txs, list)
    assert len(txs) >= 1
    tx_id = txs[0]["id"]
    detail = get(f"/architecture/transactions/{tx_id}")
    assert detail["id"] == tx_id
    assert "steps" in detail
    if detail["steps"]:
        orders = [s["step_order"] for s in detail["steps"] if s["step_order"] is not None]
        assert orders == sorted(orders)


def test_touches_can_filter_by_layer(sprint16_setup):
    touches = get("/architecture/touches", {
        "assessment_id": sprint16_setup["assessment_id"],
        "layer": "information",
    })
    assert isinstance(touches, list)
    if touches:
        assert all(t["layer"] == "information" for t in touches)


def test_chat_session_and_message_returns_transaction(sprint16_setup):
    session = post("/chat/sessions", {
        "assessment_id": sprint16_setup["assessment_id"],
        "workstream": "kubernetes",
        "title": "S16 Chat",
    })
    exchange = post(
        f"/chat/sessions/{session['id']}/messages",
        {"content": "Kubernetes tarafinda ilk bakmam gereken metrikler neler?"},
        expected=200,
    )
    assert exchange["session_id"] == session["id"]
    assert exchange.get("transaction_id")
    assert exchange["assistant_message"]["role"] == "assistant"


def test_assessment_graph_endpoint_available(sprint16_setup):
    data = get(f"/knowledge/graph/assessment/{sprint16_setup['assessment_id']}")
    assert "nodes" in data
    assert "edges" in data
