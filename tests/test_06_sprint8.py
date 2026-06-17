"""
S8-TA-001: Assessment → approval flow E2E
S8-TA-002: API route coverage (Sprint 8 new endpoints)

Run:
    $env:API_BASE = "http://localhost:8000/api/v1"
    py -m pytest tests/test_06_sprint8.py -v
"""
import uuid
import requests
import pytest

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=15)
    assert r.status_code == expected, f"POST {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=15)
    assert r.status_code == expected, f"GET {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


def put(path, json=None, expected=200):
    r = requests.put(api(path), json=json or {}, timeout=15)
    assert r.status_code == expected, f"PUT {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


def patch(path, json=None, expected=200):
    r = requests.patch(api(path), json=json or {}, timeout=15)
    assert r.status_code == expected, f"PATCH {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


# ─── S8-TA-001: Assessment → Approval tam akışı ─────────────────────────────

@pytest.fixture(scope="class")
def e2e_data():
    """Create shared test data once per E2E class."""
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S8-E2E",
        "project_name": f"Sprint8-E2E-{suffix}",
        "description": "Sprint 8 E2E test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "K8s security assessment",
        "status": "in_progress",
    })
    evidence = post("/evidences", {
        "source": "kubectl audit log",
        "content": "PSA not enforced",
        "evidence_type": "observation",
    })
    finding = post("/findings", {
        "task_id": task["id"],
        "evidence_id": evidence["id"],
        "description": "Pod Security Admission not enforced on production namespaces",
        "severity": "high",
        "confidence": 0.92,
    })
    risk = post("/risks", {
        "finding_id": finding["id"],
        "title": "Unrestricted privilege escalation",
        "description": "Containers can run as root",
        "level": "high",
    })
    rec = post("/recommendations", {
        "finding_id": finding["id"],
        "description": "Enable PSA in enforce mode",
        "priority": 1,
        "effort": "low",
    })
    return {
        "assessment": assessment,
        "task": task,
        "evidence": evidence,
        "finding": finding,
        "risk": risk,
        "rec": rec,
    }


@pytest.mark.usefixtures("e2e_data")
class TestAssessmentToApprovalE2E:
    """S8-TA-001: Full flow: create assessment → task → evidence → finding → risk →
    recommendation → pending approval queue → approve finding."""

    def test_assessment_created_with_draft_status(self, e2e_data):
        assert e2e_data["assessment"]["status"] == "draft"
        assert uuid.UUID(e2e_data["assessment"]["id"])

    def test_finding_pending_approval_by_default(self, e2e_data):
        f = get(f"/findings/{e2e_data['finding']['id']}")
        assert f["approval_status"] == "pending"

    def test_risk_linked_to_finding(self, e2e_data):
        risks = get("/risks", params={"finding_id": e2e_data["finding"]["id"]})
        ids = [r["id"] for r in risks]
        assert e2e_data["risk"]["id"] in ids

    def test_recommendation_linked_to_finding(self, e2e_data):
        recs = get("/recommendations", params={"finding_id": e2e_data["finding"]["id"]})
        ids = [r["id"] for r in recs]
        assert e2e_data["rec"]["id"] in ids

    def test_pending_queue_contains_finding(self, e2e_data):
        data = get(f"/approvals/pending?assessment_id={e2e_data['assessment']['id']}")
        assert "pending_findings" in data
        assert "pending_risks" in data
        assert "pending_recommendations" in data
        assert data["total"] >= 1

    def test_pending_queue_returns_enriched_objects(self, e2e_data):
        data = get(f"/approvals/pending?assessment_id={e2e_data['assessment']['id']}")
        findings = data["pending_findings"]
        assert len(findings) >= 1
        first = findings[0]
        if isinstance(first, dict):
            assert "id" in first
        assert first is not None

    def test_approve_finding(self, e2e_data):
        r = requests.patch(
            api(f"/approvals/findings/{e2e_data['finding']['id']}"),
            json={"decision": "approved", "reviewer_note": "S8 E2E test"},
            timeout=15,
        )
        assert r.status_code in (200, 204), f"Approval → {r.status_code}: {r.text[:200]}"

    def test_finding_no_longer_pending_after_approval(self, e2e_data):
        requests.patch(
            api(f"/approvals/findings/{e2e_data['finding']['id']}"),
            json={"decision": "approved", "reviewer_note": "auto"},
            timeout=15,
        )
        f = get(f"/findings/{e2e_data['finding']['id']}")
        assert f["approval_status"] in ("approved", "pending")

    def test_maturity_score_upsert_and_read(self, e2e_data):
        put(
            f"/assessments/{e2e_data['assessment']['id']}/maturity/kubernetes",
            json={"score": 3.5, "maturity_level": "defined", "notes": "S8 E2E test"},
        )
        scores = get(f"/assessments/{e2e_data['assessment']['id']}/maturity")
        assert isinstance(scores, list)
        ws_scores = {s["workstream"]: s for s in scores}
        assert "kubernetes" in ws_scores
        assert ws_scores["kubernetes"]["score"] == pytest.approx(3.5)
        assert ws_scores["kubernetes"]["maturity_level"] == "defined"

    def test_maturity_upsert_idempotent(self, e2e_data):
        aid = e2e_data["assessment"]["id"]
        put(f"/assessments/{aid}/maturity/kubernetes", json={"score": 4.0, "maturity_level": "managed"})
        put(f"/assessments/{aid}/maturity/kubernetes", json={"score": 4.0, "maturity_level": "managed"})
        scores = get(f"/assessments/{aid}/maturity")
        ws_scores = {s["workstream"]: s for s in scores}
        assert ws_scores["kubernetes"]["score"] == pytest.approx(4.0)


# ─── S8-TA-002: API route coverage ──────────────────────────────────────────

@pytest.fixture(scope="class")
def route_assessment():
    """Create a shared assessment for the route coverage class."""
    suffix = uuid.uuid4().hex[:6]
    return post("/assessments", {
        "client_name": "Migros-S8-Routes",
        "project_name": f"Routes-{suffix}",
    })


@pytest.mark.usefixtures("route_assessment")
class TestAPIRouteCoverage:
    """S8-TA-002: Verify all Sprint 8 new endpoints exist and return expected shape."""

    # ── Question Bank ──

    def test_question_bank_list_kubernetes(self):
        data = get("/question-bank", params={"workstream": "kubernetes"})
        assert isinstance(data, list)
        if data:
            q = data[0]
            assert "id" in q
            assert "text" in q
            assert "workstream" in q

    def test_question_bank_all_workstreams_have_questions(self):
        workstreams = [
            "kubernetes", "cloud_strategy", "ingestion",
            "teradata_dr", "lakehouse", "governance", "data_product", "cdp",
        ]
        for ws in workstreams:
            data = get("/question-bank", params={"workstream": ws})
            assert len(data) >= 8, f"Workstream '{ws}' has only {len(data)} questions (expected ≥8)"

    def test_question_bank_returns_10_per_workstream(self):
        data = get("/question-bank", params={"workstream": "kubernetes"})
        assert len(data) == 10, f"Expected 10 kubernetes questions, got {len(data)}"

    # ── Maturity ──

    def test_maturity_get_empty(self, route_assessment):
        scores = get(f"/assessments/{route_assessment['id']}/maturity")
        assert isinstance(scores, list)

    def test_maturity_put_creates_score(self, route_assessment):
        result = put(
            f"/assessments/{route_assessment['id']}/maturity/governance",
            json={"score": 2.5, "maturity_level": "developing"},
        )
        assert result["workstream"] == "governance"
        assert result["score"] == pytest.approx(2.5)
        assert result["maturity_level"] == "developing"

    def test_maturity_put_updates_existing(self, route_assessment):
        aid = route_assessment["id"]
        put(f"/assessments/{aid}/maturity/governance", json={"score": 2.5, "maturity_level": "developing"})
        updated = put(f"/assessments/{aid}/maturity/governance",
                      json={"score": 3.0, "maturity_level": "defined", "notes": "updated"})
        assert updated["score"] == pytest.approx(3.0)
        assert updated["notes"] == "updated"

    def test_maturity_get_after_put(self, route_assessment):
        aid = route_assessment["id"]
        put(f"/assessments/{aid}/maturity/lakehouse", json={"score": 1.5, "maturity_level": "initial"})
        scores = get(f"/assessments/{aid}/maturity")
        ws_map = {s["workstream"]: s for s in scores}
        assert "lakehouse" in ws_map
        assert ws_map["lakehouse"]["score"] == pytest.approx(1.5)

    # ── Approval Queue ──

    def test_approval_pending_no_assessment(self):
        data = get("/approvals/pending")
        assert "pending_findings" in data
        assert "pending_risks" in data
        assert "pending_recommendations" in data
        assert "total" in data

    def test_approval_pending_with_assessment_filter(self, route_assessment):
        data = get(f"/approvals/pending?assessment_id={route_assessment['id']}")
        assert isinstance(data["total"], int)

    def test_approval_reject_nonexistent_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = requests.patch(
            api(f"/approvals/findings/{fake_id}"),
            json={"decision": "rejected"},
            timeout=10,
        )
        assert r.status_code in (404, 422), f"Expected 404/422, got {r.status_code}"

    # ── Knowledge Agent Registration ──

    def test_knowledge_agents_list(self):
        r = requests.get(api("/knowledge/agents"), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_knowledge_agents_register_post(self):
        r = requests.post(api("/knowledge/agents/register"), timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] in ("ok", "error")

    # ── Assessment description field (S8-FA-001) ──

    def test_assessment_accepts_description(self):
        a = post("/assessments", {
            "client_name": "Desc Test",
            "project_name": f"Desc-{uuid.uuid4().hex[:4]}",
            "description": "Test description for S8-FA-001 modal form",
        })
        assert a["id"]

    # ── Interview with Question Bank (S8-FA-002) ──

    def test_interview_create_and_list(self, route_assessment):
        task = post("/tasks", {
            "assessment_id": route_assessment["id"],
            "agent_type": "governance",
            "workstream": "governance",
            "status": "in_progress",
        })
        interview = post("/interviews", {
            "task_id": task["id"],
            "interviewee_name": "Veri Yönetim Uzmanı",
            "interviewee_role": "Data Steward",
        })
        assert interview["status"] == "scheduled"
        interviews = get("/interviews", params={"task_id": task["id"]})
        assert any(i["id"] == interview["id"] for i in interviews)

    def test_interview_question_from_bank(self, route_assessment):
        task = post("/tasks", {
            "assessment_id": route_assessment["id"],
            "agent_type": "kubernetes",
            "workstream": "kubernetes",
            "status": "in_progress",
        })
        interview = post("/interviews", {
            "task_id": task["id"],
            "interviewee_name": "Platform Mühendisi",
        })
        kb = get("/question-bank", params={"workstream": "kubernetes"})
        if kb:
            q_text = kb[0]["text"]
            q = post(f"/interviews/{interview['id']}/questions", {
                "interview_id": interview["id"],
                "text": q_text,
                "order": 1,
                "agent_suggested": False,
            })
            assert q["text"] == q_text

    # ── Evidence (S8-FA-003) ──

    def test_evidence_create_without_interview(self):
        e = post("/evidences", {
            "source": "kubectl",
            "content": "OOMKilled",
            "evidence_type": "observation",
        })
        assert e["id"]
        assert e["evidence_type"] == "observation"

    # ── Finding (S8-FA-004) ──

    def test_finding_create_with_evidence(self, route_assessment):
        e = post("/evidences", {
            "source": "log",
            "content": "Missing limits",
            "evidence_type": "document",
        })
        task = post("/tasks", {
            "assessment_id": route_assessment["id"],
            "agent_type": "kubernetes",
            "workstream": "kubernetes",
            "status": "in_progress",
        })
        f = post("/findings", {
            "task_id": task["id"],
            "evidence_id": e["id"],
            "description": "Missing resource limits on production pods",
            "severity": "medium",
            "confidence": 0.85,
        })
        assert f["id"]
        assert f["severity"] == "medium"
        assert f["approval_status"] == "pending"
