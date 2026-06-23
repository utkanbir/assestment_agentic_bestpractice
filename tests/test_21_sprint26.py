"""
Sprint 26 API smoke tests:
- assessment copy/paste + consultant fields on duplicate
- generate-summary mock on empty/failure
- consultant CRUD + answer with consultant
- ontology export.ttl + doc upload learning_summary
- agent training consultant_id + training-events
- cloud_strategy evaluate
- architecture layers link_mode + health/db
- simulation multi-step + stop
- report consultant_opinions + batch ai-generate
"""
import io
import json
import time
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
def sprint26_source():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S26",
        "project_name": f"Sprint26-{suffix}",
    })
    consultant = post("/consultants", {
        "first_name": "Ayşe",
        "last_name": "Danışman",
        "role": "Architect",
    })
    post(f"/assessments/{assessment['id']}/consultants", {"consultant_id": consultant["id"]})
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S26",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "S26"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "DR stratejisi nedir?",
        "order": 1,
        "agent_suggested": False,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "Aktif-pasif DR mevcut.",
        "consultant_id": consultant["id"],
        "consultant_comment": "DR eksikleri var.",
    })
    return {
        "assessment_id": assessment["id"],
        "consultant_id": consultant["id"],
        "question_id": question["id"],
        "answer_id": answer["id"],
    }


def test_duplicate_copies_consultant_fields(sprint26_source):
    dup = post(f"/assessments/{sprint26_source['assessment_id']}/duplicate", {
        "include_qa": True,
        "include_tasks": True,
    })
    tasks = get("/tasks", params={"assessment_id": dup["id"]})
    interviews = get("/interviews", params={"task_id": tasks[0]["id"]})
    questions = get(f"/interviews/{interviews[0]['id']}/questions")
    answers = get(f"/interviews/questions/{questions[0]['id']}/answers")
    assert answers[0].get("consultant_id") == sprint26_source["consultant_id"]
    assert "DR eksik" in (answers[0].get("consultant_comment") or "")


def test_consultant_crud_and_assign(sprint26_source):
    consultants = get(f"/assessments/{sprint26_source['assessment_id']}/consultants")
    assert any(c["id"] == sprint26_source["consultant_id"] for c in consultants)
    all_consultants = get("/consultants")
    assert len(all_consultants) >= 1


def test_answer_with_consultant_persisted(sprint26_source):
    answers = get(f"/interviews/questions/{sprint26_source['question_id']}/answers")
    assert answers[0]["consultant_id"] == sprint26_source["consultant_id"]
    assert "DR eksik" in answers[0].get("consultant_comment", "")


def test_generate_summary_empty_mock():
    suffix = uuid.uuid4().hex[:6]
    empty = post("/assessments", {
        "client_name": "Empty-S26",
        "project_name": f"NoData-{suffix}",
    })
    data = post(f"/orchestrator/{empty['id']}/generate-summary", expected=200)
    assert data["summary"]
    assert len(data["summary"]) > 10


def test_generate_summary_export_fields():
    suffix = uuid.uuid4().hex[:6]
    empty = post("/assessments", {
        "client_name": "Export-S26",
        "project_name": f"Export-{suffix}",
    })
    data = post(f"/orchestrator/{empty['id']}/generate-summary", expected=200)
    assert isinstance(data["summary"], str)
    assert data["summary"].strip()


def test_ontology_export_ttl():
    r = requests.get(api("/knowledge/ontology/export.ttl"), timeout=30)
    assert r.status_code == 200
    assert "text/turtle" in r.headers.get("content-type", "")
    assert "@prefix" in r.text or "aakp:" in r.text


def test_agent_training_consultant_and_events(sprint26_source):
    ev = post("/agents/kubernetes/train/aaha/answer", {
        "question": "Test soru?",
        "answer": "Test yanıt.",
        "consultant_id": sprint26_source["consultant_id"],
    }, expected=201)
    assert ev["consultant_id"] == sprint26_source["consultant_id"]
    events = get("/agents/kubernetes/training-events")
    assert any(e["id"] == ev["id"] for e in events)


def test_doc_upload_returns_summary():
    content = b"Kubernetes RBAC policy: cluster-admin restricted."
    files = {"file": ("s26-policy.txt", io.BytesIO(content), "text/plain")}
    r = requests.post(
        api("/agents/kubernetes/documents"),
        files=files,
        data={"description": "S26 upload test"},
        timeout=60,
    )
    assert r.status_code == 201, r.text[:300]
    body = r.json()
    assert body.get("learning_summary")
    assert body["learning_summary"].get("chunks", 0) >= 1


def test_evaluate_non_kubernetes_ws():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Cloud-S26",
        "project_name": f"Cloud-{suffix}",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "cloud_strategy",
        "workstream": "cloud_strategy",
        "scope": "S26 cloud",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "S26"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Bulut stratejiniz nedir?",
        "order": 1,
        "agent_suggested": False,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "Multi-cloud hybrid yaklaşım kullanıyoruz.",
    })
    result = post(f"/interviews/answers/{answer['id']}/evaluate", expected=200)
    assert result.get("evaluation") or result.get("score") is not None


def test_architecture_layers_link_mode():
    data = get("/architecture/layers")
    techs = [t for layer in data["layers"] for t in layer["technologies"]]
    pg = next(t for t in techs if t["id"] == "postgresql")
    assert pg["console_url"] == "/health/db"
    minio = next(t for t in techs if t["id"] == "minio")
    assert minio.get("link_mode") == "internal"


def test_health_db():
    base = API_BASE.rsplit("/api/v1", 1)[0]
    r = requests.get(f"{base}/health/db", timeout=15)
    assert r.status_code == 200
    assert r.json().get("db") == "connected"


def test_simulation_multi_step_progress():
    suffix = uuid.uuid4().hex[:6]
    started = post("/assessments/simulated", {
        "client_name": "Sim-S26",
        "project_name": f"Sim26-{suffix}",
        "company_profile": {"industry": "perakende", "size": "buyuk"},
        "max_workstreams": 1,
        "max_questions_per_workstream": 2,
    })
    assessment_id = started["id"]
    deadline = time.time() + 180
    evaluated = 0
    while time.time() < deadline:
        st = get(f"/assessments/{assessment_id}/simulation/status")
        progress = st.get("simulation_progress") or {}
        evaluated = progress.get("questions_evaluated", 0)
        if evaluated >= 2:
            break
        if st.get("simulation_status") in ("completed", "failed", "stopped"):
            break
        time.sleep(2)
    assert evaluated >= 2, f"expected >=2 evaluated, got {evaluated}"


def test_simulation_stop():
    suffix = uuid.uuid4().hex[:6]
    started = post("/assessments/simulated", {
        "client_name": "Stop-S26",
        "project_name": f"Stop26-{suffix}",
        "company_profile": {"industry": "perakende", "size": "buyuk"},
        "max_workstreams": 1,
        "max_questions_per_workstream": 3,
    })
    assessment_id = started["id"]
    time.sleep(3)
    stop = post(f"/assessments/{assessment_id}/simulation/stop", expected=200)
    assert stop["simulation_status"] == "stopped"


def test_report_consultant_opinions(sprint26_source):
    report = post(f"/reports/assessment/{sprint26_source['assessment_id']}/compose", expected=200)
    content = json.loads(report["content_json"])
    section = content["sections"][0]
    section["consultant_opinions"] = [
        {"consultant_id": sprint26_source["consultant_id"], "comment": "Görüş 1"},
        {"consultant_id": sprint26_source["consultant_id"], "comment": "Görüş 2"},
    ]
    updated = patch(f"/reports/{report['id']}", {"content_json": json.dumps(content)})
    saved = json.loads(updated["content_json"])
    opinions = saved["sections"][0].get("consultant_opinions", [])
    assert len(opinions) >= 2


def test_report_batch_ai(sprint26_source):
    report = post(f"/reports/assessment/{sprint26_source['assessment_id']}/compose", expected=200)
    result = post(
        f"/reports/{report['id']}/ai-generate",
        json={"mode": "generate"},
        expected=200,
    )
    assert result["total_sections"] >= 1
    assert len(result["updated_sections"]) >= 1
