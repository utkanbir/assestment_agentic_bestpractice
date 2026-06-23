"""Product router unit + chat integration (Question Bank count intent)."""
import uuid

import pytest
import requests

from app.services.product_router import (
    detect_question_bank_count_intent,
    extract_workstream_hint,
)
from conftest import API_BASE


def test_detect_question_bank_count_intent_positive():
    assert detect_question_bank_count_intent("Kaç soru tanımlı?")
    assert detect_question_bank_count_intent("kubernetes için kaç soru var")
    assert detect_question_bank_count_intent("question bank kaç soru içeriyor")


def test_detect_question_bank_count_intent_negative():
    assert not detect_question_bank_count_intent("Kaç assessment var?")
    assert not detect_question_bank_count_intent("Merhaba")


def test_extract_workstream_hint_from_message():
    assert extract_workstream_hint("kubernetes soru sayısı", "general") == "kubernetes"
    assert extract_workstream_hint("lakehouse kaç soru", "general") == "lakehouse"


def test_extract_workstream_hint_from_session():
    assert extract_workstream_hint("kaç soru tanımlı", "governance") == "governance"


@pytest.fixture(scope="module")
def product_router_chat_setup():
    suffix = uuid.uuid4().hex[:6]
    r = requests.post(
        f"{API_BASE}/assessments",
        json={
            "client_name": "Migros-PR",
            "project_name": f"ProductRouter-{suffix}",
            "description": "Product router test",
        },
        timeout=30,
    )
    assert r.status_code == 201
    return {"assessment_id": r.json()["id"]}


def test_chat_question_bank_count_via_router(product_router_chat_setup):
    bank = requests.get(
        f"{API_BASE}/question-bank",
        params={"workstream": "kubernetes"},
        timeout=30,
    )
    assert bank.status_code == 200
    expected_k8s = len(bank.json())

    session = requests.post(
        f"{API_BASE}/chat/sessions",
        json={
            "assessment_id": product_router_chat_setup["assessment_id"],
            "workstream": "kubernetes",
            "title": "Product router test",
        },
        timeout=30,
    )
    assert session.status_code == 201
    exchange = requests.post(
        f"{API_BASE}/chat/sessions/{session.json()['id']}/messages",
        json={"content": "kubernetes için kaç soru tanımlı?"},
        timeout=90,
    )
    assert exchange.status_code == 200
    body = exchange.json()
    reply = body["assistant_message"]["content"].lower()
    assert "question bank" in reply
    assert str(expected_k8s) in reply or expected_k8s == 0
    trace = body.get("layer_trace") or []
    components = {t.get("component") for t in trace}
    assert "question_bank" in components or "product_router" in components
