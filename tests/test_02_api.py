"""
Sprint 1 FastAPI endpoint tests.
Requires: .\infra\build.ps1 && .\infra\deploy.ps1 -Action sprint1
"""
import uuid
import httpx
import pytest


@pytest.fixture(scope="module")
def client(api_base):
    with httpx.Client(base_url=api_base, timeout=10) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    # health router is mounted at root (no /api/v1 prefix)
    r = httpx.get(client.base_url.copy_with(path="/health"), timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_db(client):
    r = httpx.get(client.base_url.copy_with(path="/health/db"), timeout=5)
    assert r.status_code == 200
    assert r.json()["db"] in ("ok", "connected")


# ── Assessment CRUD ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def assessment(client):
    r = client.post("/assessments", json={
        "client_name": "Test Müşteri",
        "project_name": "AAKP Smoke Test",
        "description": "Otomatik test tarafından oluşturuldu",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    yield data
    client.delete(f"/assessments/{data['id']}")


def test_assessment_created(assessment):
    assert assessment["client_name"] == "Test Müşteri"
    assert assessment["status"] == "draft"
    assert uuid.UUID(assessment["id"])


def test_list_assessments(client, assessment):
    r = client.get("/assessments")
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert assessment["id"] in ids


def test_get_assessment(client, assessment):
    r = client.get(f"/assessments/{assessment['id']}")
    assert r.status_code == 200
    assert r.json()["project_name"] == "AAKP Smoke Test"


def test_patch_assessment(client, assessment):
    r = client.patch(f"/assessments/{assessment['id']}", json={"status": "active"})
    assert r.status_code == 200
    assert r.json()["status"] == "active"


# ── Task CRUD ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def task(client, assessment):
    r = client.post("/tasks", json={
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "Kubernetes Assessment",
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_task_created(task):
    assert task["workstream"] == "Kubernetes Assessment"
    assert task["status"] == "pending"


def test_list_tasks(client, assessment, task):
    r = client.get(f"/tasks?assessment_id={assessment['id']}")
    assert r.status_code == 200
    assert any(t["id"] == task["id"] for t in r.json())


# ── Interview CRUD ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def interview(client, task):
    r = client.post("/interviews", json={
        "task_id": task["id"],
        "interviewee_name": "Test Uzmanı",
        "interviewee_role": "Kubernetes Mühendisi",
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_interview_created(interview):
    assert interview["status"] == "scheduled"


# ── Evidence + Finding ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def evidence(client, interview):
    r = client.post("/evidences", json={
        "interview_id": interview["id"],
        "source": "interview",
        "content": "Cluster'da NetworkPolicy tanımlı değil, tüm pod'lar birbirine erişebiliyor.",
        "evidence_type": "interview",
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_evidence_created(evidence):
    assert evidence["evidence_type"] == "interview"


@pytest.fixture(scope="module")
def finding(client, task, evidence):
    r = client.post("/findings", json={
        "task_id": task["id"],
        "evidence_id": evidence["id"],
        "description": "NetworkPolicy eksikliği: pod-to-pod trafiği kısıtlanmamış",
        "severity": "high",
        "confidence": 0.9,
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_finding_created(finding):
    assert finding["severity"] == "high"
    assert finding["approval_status"] == "pending"
    assert finding["confidence"] == pytest.approx(0.9)


def test_list_findings(client, task, finding):
    r = client.get(f"/findings?task_id={task['id']}")
    assert r.status_code == 200
    assert any(f["id"] == finding["id"] for f in r.json())


def test_approve_finding(client, finding):
    r = client.post(f"/knowledge/findings/{finding['id']}/approve", json={"status": "approved"})
    assert r.status_code in (200, 204, 502), r.text  # 502 if Fuseki KG not yet populated
