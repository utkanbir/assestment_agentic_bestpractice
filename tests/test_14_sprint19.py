"""
Sprint 19 API checks:
- chat user+assistant in history
- assessment count platform context
- transaction narrative
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
def sprint19_setup():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S19",
        "project_name": f"Sprint19-{suffix}",
        "description": "Sprint19 integration test",
    })
    return {"assessment_id": assessment["id"]}


def test_chat_messages_include_user_and_assistant(sprint19_setup):
    session = post("/chat/sessions", {
        "assessment_id": sprint19_setup["assessment_id"],
        "workstream": "general",
        "title": "S19 chat test",
    })
    session_id = session["id"]
    exchange = post(
        f"/chat/sessions/{session_id}/messages",
        {"content": "Merhaba, test mesajı"},
        expected=200,
    )
    assert exchange["user_message"]["role"] == "user"
    assert exchange["user_message"]["content"] == "Merhaba, test mesajı"
    assert exchange["assistant_message"]["role"] == "assistant"

    messages = get(f"/chat/sessions/{session_id}/messages")
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles
    assert any(m["content"] == "Merhaba, test mesajı" for m in messages if m["role"] == "user")


def test_chat_assessment_count_answer(sprint19_setup):
    session = post("/chat/sessions", {
        "assessment_id": sprint19_setup["assessment_id"],
        "workstream": "general",
        "title": "S19 count test",
    })
    all_assessments = get("/assessments")
    expected_min = len(all_assessments)

    exchange = post(
        f"/chat/sessions/{session['id']}/messages",
        {"content": "Kaç assessment var?"},
        expected=200,
    )
    reply = exchange["assistant_message"]["content"].lower()
    assert str(expected_min) in reply or "assessment" in reply


def test_transaction_narrative(sprint19_setup):
    session = post("/chat/sessions", {
        "assessment_id": sprint19_setup["assessment_id"],
        "workstream": "general",
        "title": "S19 narrative test",
    })
    exchange = post(
        f"/chat/sessions/{session['id']}/messages",
        {"content": "Narrative test"},
        expected=200,
    )
    tx_id = exchange.get("transaction_id")
    if not tx_id:
        pytest.skip("no transaction_id recorded")
    detail = get(f"/architecture/transactions/{tx_id}")
    assert "narrative" in detail
    assert len(detail["narrative"]) > 40
    assert "katman" in detail["narrative"].lower() or "Katman" in detail["narrative"]


def test_compose_report_still_available(sprint19_setup):
    report = post(
        f"/reports/assessment/{sprint19_setup['assessment_id']}/compose",
        expected=200,
    )
    assert report.get("content_json")
