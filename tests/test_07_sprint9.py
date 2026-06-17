"""
S9-TA-001: Onay → Executive Summary → Roadmap tam akış E2E testi
S9-TA-002: Sprint 9 yeni endpoint şekil doğrulama (route coverage)

Run:
    $env:API_BASE = "http://localhost:8000/api/v1"
    py -m pytest tests/test_07_sprint9.py -v
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


def patch(path, json=None, expected=200):
    r = requests.patch(api(path), json=json or {}, timeout=15)
    assert r.status_code == expected, f"PATCH {path} → {r.status_code}: {r.text[:300]}"
    return r.json()


# ─── S9-TA-001: Onay → Summary → Roadmap tam akışı ──────────────────────────

@pytest.fixture(scope="class")
def e2e_s9_data():
    """Create shared test data once per E2E class (Sprint 9)."""
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S9-E2E",
        "project_name": f"Sprint9-E2E-{suffix}",
        "description": "Sprint 9 E2E test — approval to executive summary full flow",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "K8s security & compliance assessment",
        "status": "in_progress",
    })
    evidence = post("/evidences", {
        "source": "kubectl audit log",
        "content": "RBAC misconfiguration detected in production namespace",
        "evidence_type": "observation",
    })
    finding = post("/findings", {
        "task_id": task["id"],
        "evidence_id": evidence["id"],
        "description": "Overly permissive ClusterRole bindings exposing sensitive API groups",
        "severity": "high",
        "confidence": 0.95,
    })
    risk = post("/risks", {
        "finding_id": finding["id"],
        "title": "Privilege escalation via misconfigured RBAC",
        "description": "Attackers can escalate privileges through wildcard ClusterRole bindings",
        "level": "high",
    })
    rec = post("/recommendations", {
        "finding_id": finding["id"],
        "description": "Restrict ClusterRole bindings to least-privilege principle",
        "priority": 1,
        "effort": "medium",
    })
    return {
        "assessment": assessment,
        "task": task,
        "evidence": evidence,
        "finding": finding,
        "risk": risk,
        "rec": rec,
    }


@pytest.mark.usefixtures("e2e_s9_data")
class TestApprovalToSummaryE2E:
    """S9-TA-001: Tam akış: Assessment → Finding → Approve → Generate Summary → Roadmap."""

    def test_finding_starts_as_pending(self, e2e_s9_data):
        f = get(f"/findings/{e2e_s9_data['finding']['id']}")
        assert f["approval_status"] == "pending", (
            f"Finding should start as 'pending', got '{f['approval_status']}'"
        )

    def test_approve_finding_workflow(self, e2e_s9_data):
        r = requests.patch(
            api(f"/approvals/findings/{e2e_s9_data['finding']['id']}"),
            json={"decision": "approved", "reviewer_note": "S9 E2E auto-approve"},
            timeout=15,
        )
        assert r.status_code in (200, 204), (
            f"Approval PATCH → {r.status_code}: {r.text[:200]}"
        )

    def test_finding_is_approved(self, e2e_s9_data):
        # Only GET — do not re-approve to avoid 409 conflict
        f = get(f"/findings/{e2e_s9_data['finding']['id']}")
        assert f["approval_status"] == "approved", (
            f"Finding should be 'approved' after approval, got '{f['approval_status']}'"
        )

    def test_generate_summary_no_findings_returns_422(self):
        """An assessment with no findings should return 422 from generate-summary."""
        suffix = uuid.uuid4().hex[:6]
        empty_assessment = post("/assessments", {
            "client_name": "Migros-S9-Empty",
            "project_name": f"Sprint9-Empty-{suffix}",
            "description": "Empty assessment for 422 check",
        })
        r = requests.post(
            api(f"/orchestrator/{empty_assessment['id']}/generate-summary"),
            timeout=15,
        )
        assert r.status_code == 422, (
            f"Expected 422 for empty assessment, got {r.status_code}: {r.text[:200]}"
        )

    def test_generate_summary_with_findings(self, e2e_s9_data):
        aid = e2e_s9_data["assessment"]["id"]
        r = requests.post(api(f"/orchestrator/{aid}/generate-summary"), timeout=30)
        assert r.status_code == 200, (
            f"generate-summary → {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert data["assessment_id"] == aid
        assert isinstance(data["summary"], str) and len(data["summary"]) > 0, (
            "summary field must be a non-empty string"
        )
        assert data["total_risks"] > 0, (
            f"total_risks should be > 0 after adding a risk, got {data['total_risks']}"
        )
        assert "generated_at" in data
        assert "critical_count" in data
        assert "dependency_count" in data
        assert "conflict_count" in data
        # Store summary for later tests
        e2e_s9_data["summary"] = data

    def test_executive_summary_readable_after_generate(self, e2e_s9_data):
        aid = e2e_s9_data["assessment"]["id"]
        data = get(f"/orchestrator/{aid}/executive-summary")
        assert data["assessment_id"] == aid
        assert isinstance(data["summary"], str) and len(data["summary"]) > 0, (
            "GET executive-summary must return a non-empty summary string"
        )
        assert "total_risks" in data
        assert "generated_at" in data

    def test_risk_heatmap_returns_list(self, e2e_s9_data):
        aid = e2e_s9_data["assessment"]["id"]
        data = get(f"/orchestrator/{aid}/risk-heatmap")
        assert isinstance(data, list), (
            f"risk-heatmap must return a list, got {type(data)}"
        )

    def test_risk_heatmap_cell_shape(self, e2e_s9_data):
        aid = e2e_s9_data["assessment"]["id"]
        data = get(f"/orchestrator/{aid}/risk-heatmap")
        if not data:
            pytest.skip("risk-heatmap returned empty list — cell shape cannot be verified")
        for cell in data:
            assert "capability_area" in cell, f"Missing 'capability_area' in cell: {cell}"
            assert "severity" in cell, f"Missing 'severity' in cell: {cell}"
            assert "risk_count" in cell, f"Missing 'risk_count' in cell: {cell}"

    def test_roadmap_before_rec_approval(self, e2e_s9_data):
        """Roadmap should not contain the recommendation before it is approved."""
        aid = e2e_s9_data["assessment"]["id"]
        data = get(f"/orchestrator/{aid}/roadmap")
        assert isinstance(data, list), (
            f"roadmap must return a list, got {type(data)}"
        )
        rec_id = e2e_s9_data["rec"]["id"]
        approved_ids = [item.get("recommendation_id") or item.get("id") for item in data]
        assert rec_id not in approved_ids, (
            "Recommendation should not appear in roadmap before being approved"
        )

    def test_approve_recommendation_and_roadmap(self, e2e_s9_data):
        rec_id = e2e_s9_data["rec"]["id"]
        aid = e2e_s9_data["assessment"]["id"]

        # Approve the recommendation
        r = requests.patch(
            api(f"/approvals/recommendations/{rec_id}"),
            json={"decision": "approved", "reviewer_note": "S9 roadmap E2E"},
            timeout=15,
        )
        assert r.status_code in (200, 204), (
            f"Rec approval → {r.status_code}: {r.text[:200]}"
        )

        # Roadmap must now include an entry referencing this recommendation
        roadmap = get(f"/orchestrator/{aid}/roadmap")
        assert isinstance(roadmap, list), "roadmap must return a list"
        assert len(roadmap) >= 1, (
            "Roadmap must contain at least one item after approving a recommendation"
        )
        roadmap_ids = [item.get("recommendation_id") or item.get("id") for item in roadmap]
        assert rec_id in roadmap_ids, (
            f"Approved recommendation {rec_id} not found in roadmap: {roadmap_ids}"
        )


# ─── S9-TA-002: Endpoint şekil doğrulama (route coverage) ───────────────────

@pytest.fixture(scope="class")
def s9_route_assessment():
    """Create a minimal assessment for Sprint 9 route coverage tests."""
    suffix = uuid.uuid4().hex[:6]
    return post("/assessments", {
        "client_name": "Migros-S9-Routes",
        "project_name": f"S9Routes-{suffix}",
        "description": "Sprint 9 route coverage check",
    })


@pytest.mark.usefixtures("s9_route_assessment")
class TestOrchestratorEndpointShape:
    """S9-TA-002: Verify all Sprint 9 orchestrator endpoints exist and return expected shape."""

    def test_generate_summary_endpoint_exists(self, s9_route_assessment):
        """POST to empty assessment returns 422 — proves the endpoint is wired up."""
        r = requests.post(
            api(f"/orchestrator/{s9_route_assessment['id']}/generate-summary"),
            timeout=15,
        )
        assert r.status_code == 422, (
            f"Expected 422 (no findings) from generate-summary endpoint, "
            f"got {r.status_code}: {r.text[:200]}"
        )

    def test_risk_heatmap_endpoint_exists(self, s9_route_assessment):
        data = get(f"/orchestrator/{s9_route_assessment['id']}/risk-heatmap")
        assert isinstance(data, list), (
            f"risk-heatmap must return a list, got {type(data)}"
        )

    def test_roadmap_endpoint_exists(self, s9_route_assessment):
        data = get(f"/orchestrator/{s9_route_assessment['id']}/roadmap")
        assert isinstance(data, list), (
            f"roadmap must return a list, got {type(data)}"
        )

    def test_executive_summary_404_when_no_report(self, s9_route_assessment):
        """New assessment with no generated summary must return 404."""
        r = requests.get(
            api(f"/orchestrator/{s9_route_assessment['id']}/executive-summary"),
            timeout=15,
        )
        assert r.status_code == 404, (
            f"Expected 404 for missing executive summary, "
            f"got {r.status_code}: {r.text[:200]}"
        )

    def test_approval_findings_patch_shape(self, s9_route_assessment):
        """PATCH /approvals/findings/{fake_id} on unknown ID returns 404 or 422."""
        fake_id = str(uuid.uuid4())
        r = requests.patch(
            api(f"/approvals/findings/{fake_id}"),
            json={"decision": "approved"},
            timeout=10,
        )
        assert r.status_code in (404, 422), (
            f"Expected 404 or 422 for unknown finding approval, got {r.status_code}"
        )

    def test_approval_risks_patch_shape(self, s9_route_assessment):
        """PATCH /approvals/risks/{fake_id} on unknown ID returns 404 or 422."""
        fake_id = str(uuid.uuid4())
        r = requests.patch(
            api(f"/approvals/risks/{fake_id}"),
            json={"decision": "approved"},
            timeout=10,
        )
        assert r.status_code in (404, 422), (
            f"Expected 404 or 422 for unknown risk approval, got {r.status_code}"
        )

    def test_approval_recommendations_patch_shape(self, s9_route_assessment):
        """PATCH /approvals/recommendations/{fake_id} on unknown ID returns 404 or 422."""
        fake_id = str(uuid.uuid4())
        r = requests.patch(
            api(f"/approvals/recommendations/{fake_id}"),
            json={"decision": "approved"},
            timeout=10,
        )
        assert r.status_code in (404, 422), (
            f"Expected 404 or 422 for unknown recommendation approval, got {r.status_code}"
        )
