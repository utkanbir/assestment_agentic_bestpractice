"""
Sprint 24 API checks:
- AAHA training question + answer
- Text know-how ingest
- Agent ontology graph
"""
import uuid

import pytest
import requests

from conftest import API_BASE

WORKSTREAM = "kubernetes"


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=90)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:400]}"
    return r.json()


def get(path, expected=200):
    r = requests.get(api(path), timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def test_aaha_generate_question():
    data = post(f"/agents/{WORKSTREAM}/train/aaha", expected=200)
    assert data["question"]
    assert "?" in data["question"] or len(data["question"]) > 10


def test_aaha_submit_answer():
    q = post(f"/agents/{WORKSTREAM}/train/aaha", expected=200)
    suffix = uuid.uuid4().hex[:6]
    ev = post(f"/agents/{WORKSTREAM}/train/aaha/answer", {
        "question": q["question"],
        "answer": f"Test know-how yanıtı {suffix}: 12 node HA cluster, ArgoCD ile deploy.",
    })
    assert ev["mode"] == "aaha"
    assert ev["workstream"] == WORKSTREAM
    assert ev["question_text"]
    assert "know-how" in ev["answer_text"]


def test_text_knowledge_ingest():
    suffix = uuid.uuid4().hex[:6]
    ev = post(f"/agents/{WORKSTREAM}/train/text", {
        "content": f"Lakehouse best practice {suffix}: Delta format, medallion architecture, "
                   "bronze-silver-gold katmanları. Günlük 2TB veri işlenir.",
    })
    assert ev["mode"] == "text"
    assert ev["workstream"] == WORKSTREAM
    assert "medallion" in ev["answer_text"]


def test_agent_graph():
    post(f"/agents/{WORKSTREAM}/train/text", {
        "content": f"Graph test bilgisi {uuid.uuid4().hex[:4]}",
    })
    graph = get(f"/agents/{WORKSTREAM}/graph")
    assert "nodes" in graph
    assert "edges" in graph
    types = {n["type"] for n in graph["nodes"]}
    assert "agent" in types
    assert "ontology" in types
    agent_nodes = [n for n in graph["nodes"] if n["type"] == "agent"]
    assert len(agent_nodes) == 1
    assert agent_nodes[0]["id"] == f"agent:{WORKSTREAM}"


def test_unknown_workstream_404():
    r = requests.post(api("/agents/invalid_ws/train/aaha"), json={}, timeout=30)
    assert r.status_code == 404
