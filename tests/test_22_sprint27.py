"""
Sprint 27 API tests:
- simulation stop leaves task in_progress (no premature complete)
- doc upload learning_summary preview field
- ontology export merged graph + include_instances param
- health/db via /health/ prefix
- layers OpenMetadata /openmetadata/ URL
"""
import io
import time
import uuid

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


def test_simulation_stop_task_not_completed():
    suffix = uuid.uuid4().hex[:6]
    started = post("/assessments/simulated", {
        "client_name": "Stop-S27",
        "project_name": f"Stop27-{suffix}",
        "company_profile": {"industry": "perakende", "size": "buyuk"},
        "max_workstreams": 2,
        "max_questions_per_workstream": 3,
    })
    assessment_id = started["id"]
    deadline = time.time() + 30
    while time.time() < deadline:
        st = get(f"/assessments/{assessment_id}/simulation/status")
        if st.get("simulation_status") == "running":
            break
        time.sleep(0.5)
    stop = post(f"/assessments/{assessment_id}/simulation/stop", expected=200)
    assert stop["simulation_status"] == "stopped"
    tasks = get("/tasks", params={"assessment_id": assessment_id})
    assert tasks, "expected at least one task from simulation"
    in_progress = [t for t in tasks if t["status"] == "in_progress"]
    assert in_progress, f"expected in_progress task after stop, got {[t['status'] for t in tasks]}"


def test_doc_upload_preview_field():
    content = b"Sprint 27 preview test: Kubernetes network policies enforce zero-trust segmentation."
    files = {"file": ("s27-preview.txt", io.BytesIO(content), "text/plain")}
    r = requests.post(
        api("/agents/kubernetes/documents"),
        files=files,
        data={"description": "S27 preview"},
        timeout=60,
    )
    assert r.status_code == 201, r.text[:300]
    summary = r.json().get("learning_summary") or {}
    assert summary.get("preview")
    assert "Kubernetes" in summary["preview"]


def test_ontology_export_merged():
    r = requests.get(api("/knowledge/ontology/export.ttl"), timeout=30)
    assert r.status_code == 200
    assert "text/turtle" in r.headers.get("content-type", "")
    text = r.text
    assert "aakp:Assessment" in text or "Assessment" in text
    assert "arch:Capability" in text or "Capability" in text


def test_ontology_export_include_instances():
    r = requests.get(
        api("/knowledge/ontology/export.ttl"),
        params={"include_instances": "true"},
        timeout=30,
    )
    assert r.status_code == 200
    assert len(r.text) > 200


def test_health_db_prefix():
    base = API_BASE.rsplit("/api/v1", 1)[0]
    r = requests.get(f"{base}/health/db", timeout=15)
    assert r.status_code == 200
    assert r.json().get("db") == "connected"


def test_layers_openmetadata_url():
    layers = get("/architecture/layers")
    techs = [t for layer in layers["layers"] for t in layer["technologies"]]
    om = next(t for t in techs if t["id"] == "openmetadata")
    assert om["console_url"] == "/openmetadata/"
    qdrant = next(t for t in techs if t["id"] == "qdrant")
    assert qdrant.get("link_mode") == "internal"
    pg = next(t for t in techs if t["id"] == "postgresql")
    assert pg["console_url"] == "/health/db"


def test_simulation_finalize_separate():
    suffix = uuid.uuid4().hex[:6]
    started = post("/assessments/simulated", {
        "client_name": "Fin-S27",
        "project_name": f"Fin27-{suffix}",
        "company_profile": {"industry": "perakende", "size": "buyuk"},
        "max_workstreams": 1,
        "max_questions_per_workstream": 1,
    })
    assessment_id = started["id"]
    deadline = time.time() + 120
    while time.time() < deadline:
        st = get(f"/assessments/{assessment_id}/simulation/status")
        if st.get("simulation_status") in ("completed", "failed", "stopped"):
            break
        time.sleep(2)
    post(f"/assessments/{assessment_id}/simulation/stop", expected=200)
    fin = post(f"/assessments/{assessment_id}/simulation/finalize", expected=200)
    assert fin.get("report_id")
    st = get(f"/assessments/{assessment_id}/simulation/status")
    assert st.get("simulation_status") in ("finalized", "stopped", "completed")
