"""
S15-TA-001: Sprint 15 — Knowledge Architecture layer touch instrumentation

Run:
    $env:API_BASE = "http://localhost:8000/api/v1"
    py -m pytest tests/test_10_sprint15.py -v
"""
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=90)
    assert r.status_code == expected, f"POST {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=15)
    assert r.status_code == expected, f"GET {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def touch_flow_data():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S15-Touch",
        "project_name": f"Sprint15-{suffix}",
        "description": "Layer touch instrumentation test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "K8s layer touch test",
        "status": "in_progress",
    })
    interview = post("/interviews", {
        "task_id": task["id"],
        "interviewee_name": "LayerTouchTester",
    })
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "RBAC nasıl yönetiliyor?",
        "order": 1,
        "agent_suggested": False,
    })
    return {
        "assessment_id": assessment["id"],
        "interview_id": interview["id"],
        "question_id": question["id"],
    }


class TestArchitectureRegistry:
    def test_layers_endpoint_returns_four_layers(self):
        data = get("/architecture/layers")
        assert "layers" in data
        assert len(data["layers"]) == 4
        ids = {l["id"] for l in data["layers"]}
        assert ids == {"data", "information", "knowledge", "agent"}

    def test_each_layer_has_technologies(self):
        data = get("/architecture/layers")
        for layer in data["layers"]:
            assert len(layer["technologies"]) >= 3
            assert layer["namespace"].startswith("aakp-")


class TestLayerTouchOnSaveAnswer:
    def test_save_answer_records_postgresql_touch(self, touch_flow_data):
        answer = post(
            f"/interviews/questions/{touch_flow_data['question_id']}/answers",
            {"question_id": touch_flow_data["question_id"], "text": "ClusterRole kullanıyoruz."},
        )
        assert "layer_trace" in answer
        assert len(answer["layer_trace"]) >= 1
        layers = {t["layer"] for t in answer["layer_trace"]}
        techs = {t["technology"] for t in answer["layer_trace"]}
        assert "information" in layers
        assert "postgresql" in techs

        touches = get("/architecture/touches", {
            "interview_id": touch_flow_data["interview_id"],
        })
        assert any(t["operation"] == "save_answer" for t in touches)


class TestLayerTouchOnEvaluate:
    def test_evaluate_records_information_and_agent_touches(self, touch_flow_data):
        answer = post(
            f"/interviews/questions/{touch_flow_data['question_id']}/answers",
            {"question_id": touch_flow_data["question_id"], "text": "Least-privilege RBAC uyguluyoruz."},
        )
        result = post(
            f"/interviews/answers/{answer['id']}/evaluate",
            expected=200,
        )
        assert "layer_trace" in result
        assert len(result["layer_trace"]) >= 3

        layers = {t["layer"] for t in result["layer_trace"]}
        techs = {t["technology"] for t in result["layer_trace"]}
        assert "information" in layers
        assert "agent" in layers
        assert "claude" in techs
        # Sprint 16: evaluate_answer also reads ontology context from knowledge layer
        assert "knowledge" in layers
        assert "fuseki" in techs

    def test_touch_summary_by_assessment(self, touch_flow_data):
        summary = get("/architecture/touches/summary", {
            "assessment_id": touch_flow_data["assessment_id"],
        })
        assert isinstance(summary, list)
        layer_ids = {s["layer"] for s in summary}
        assert "information" in layer_ids
