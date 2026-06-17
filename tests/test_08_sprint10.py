"""
S10-TA-001: Sprint 10 E2E — Interview agent suggestion + approval + agent status

Run:
    $env:API_BASE = "http://localhost:8000/api/v1"
    py -m pytest tests/test_08_sprint10.py -v
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


# ─── Sınıf 1: Interview Suggest + Approve akışı ─────────────────────────────

@pytest.fixture(scope="class")
def suggest_flow_data():
    """Create shared test data once per class (interview suggest/approve flow)."""
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S10-Suggest",
        "project_name": f"Sprint10-{suffix}",
        "description": "Sprint 10 E2E — interview suggest-followup and approval flow",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "K8s security assessment",
        "status": "in_progress",
    })
    interview = post("/interviews", {
        "task_id": task["id"],
        "interviewee_name": "TestConsultant",
    })
    initial_question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Initial question",
        "order": 1,
        "agent_suggested": False,
    })
    return {
        "assessment": assessment,
        "task": task,
        "interview": interview,
        "initial_question": initial_question,
        # suggestion_id will be populated by test_suggest_followup_creates_pending_question
        "suggestion_id": None,
    }


@pytest.mark.usefixtures("suggest_flow_data")
class TestInterviewSuggestApproveFlow:
    """S10-TA-001: Interview agent suggestion + approval tam akışı."""

    def test_suggest_followup_creates_pending_question(self, suggest_flow_data):
        interview_id = suggest_flow_data["interview"]["id"]
        r = requests.post(api(f"/interviews/{interview_id}/suggest-followup"), json={}, timeout=15)
        assert r.status_code == 201, (
            f"POST /interviews/{interview_id}/suggest-followup → {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert "id" in data, "Response must contain 'id'"
        assert "interview_id" in data, "Response must contain 'interview_id'"
        assert "text" in data, "Response must contain 'text'"
        assert data.get("agent_suggested") is True, (
            f"agent_suggested must be True, got {data.get('agent_suggested')}"
        )
        assert data.get("approval_status") == "pending", (
            f"approval_status must be 'pending', got {data.get('approval_status')}"
        )
        # Store suggestion_id for subsequent tests
        suggest_flow_data["suggestion_id"] = data["id"]

    def test_suggest_followup_with_custom_text(self, suggest_flow_data):
        interview_id = suggest_flow_data["interview"]["id"]
        custom_text = "Kubernetes RBAC yapılandırmanızı açıklar mısınız?"
        r = requests.post(
            api(f"/interviews/{interview_id}/suggest-followup"),
            json={"text": custom_text},
            timeout=15,
        )
        assert r.status_code == 201, (
            f"POST /interviews/{interview_id}/suggest-followup (custom text) → "
            f"{r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert data.get("text") == custom_text, (
            f"text must match custom text, got '{data.get('text')}'"
        )
        assert data.get("agent_suggested") is True, (
            f"agent_suggested must be True, got {data.get('agent_suggested')}"
        )
        assert data.get("approval_status") == "pending", (
            f"approval_status must be 'pending', got {data.get('approval_status')}"
        )

    def test_list_questions_shows_pending(self, suggest_flow_data):
        interview_id = suggest_flow_data["interview"]["id"]
        data = get(f"/interviews/{interview_id}/questions")
        assert isinstance(data, list), f"GET /interviews/{interview_id}/questions must return a list"
        pending_questions = [
            q for q in data
            if q.get("agent_suggested") and q.get("approval_status") == "pending"
        ]
        assert len(pending_questions) >= 1, (
            f"Expected at least 1 pending agent_suggested question, "
            f"found {len(pending_questions)}. Questions: {data}"
        )

    def test_approve_question(self, suggest_flow_data):
        suggestion_id = suggest_flow_data.get("suggestion_id")
        assert suggestion_id is not None, (
            "suggestion_id not set — test_suggest_followup_creates_pending_question must run first"
        )
        data = patch(
            f"/interviews/questions/{suggestion_id}/approval",
            json={"action": "approved"},
        )
        assert data.get("approval_status") == "approved", (
            f"approval_status must be 'approved' after approve action, got '{data.get('approval_status')}'"
        )

    def test_reject_question(self, suggest_flow_data):
        interview_id = suggest_flow_data["interview"]["id"]
        # Create a new suggestion to reject
        r = requests.post(api(f"/interviews/{interview_id}/suggest-followup"), json={}, timeout=15)
        assert r.status_code == 201, (
            f"POST suggest-followup for reject test → {r.status_code}: {r.text[:300]}"
        )
        new_id = r.json()["id"]

        data = patch(
            f"/interviews/questions/{new_id}/approval",
            json={"action": "rejected"},
        )
        assert data.get("approval_status") == "rejected", (
            f"approval_status must be 'rejected' after reject action, got '{data.get('approval_status')}'"
        )

    def test_invalid_approval_action(self, suggest_flow_data):
        suggestion_id = suggest_flow_data.get("suggestion_id")
        assert suggestion_id is not None, (
            "suggestion_id not set — test_suggest_followup_creates_pending_question must run first"
        )
        r = requests.patch(
            api(f"/interviews/questions/{suggestion_id}/approval"),
            json={"action": "invalid_action"},
            timeout=15,
        )
        assert r.status_code == 400, (
            f"Expected HTTP 400 for invalid action, got {r.status_code}: {r.text[:300]}"
        )

    def test_approve_nonexistent_question(self, suggest_flow_data):
        fake_id = str(uuid.uuid4())
        r = requests.patch(
            api(f"/interviews/questions/{fake_id}/approval"),
            json={"action": "approved"},
            timeout=15,
        )
        assert r.status_code == 404, (
            f"Expected HTTP 404 for non-existent question, got {r.status_code}: {r.text[:300]}"
        )


# ─── Sınıf 2: Agent Status endpoint ─────────────────────────────────────────

@pytest.fixture(scope="class")
def agent_status_data():
    """Create shared test data once per class (agent status tests)."""
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S10-AgentStatus",
        "project_name": f"Sprint10-AgentStatus-{suffix}",
        "description": "Sprint 10 E2E — agent status endpoint tests",
    })
    task1 = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes_agent",
        "workstream": "kubernetes",
        "scope": "K8s assessment",
    })
    patch(f"/tasks/{task1['id']}", {"status": "in_progress"})
    task2 = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "cloud_strategy_agent",
        "workstream": "cloud_strategy",
        "scope": "Cloud strategy assessment",
        "status": "pending",
    })
    return {
        "assessment": assessment,
        "task1": task1,
        "task2": task2,
    }


@pytest.mark.usefixtures("agent_status_data")
class TestAgentStatusEndpoint:
    """S10-TA-001: GET /assessments/{id}/agent-status endpoint doğrulama."""

    def test_agent_status_returns_list(self, agent_status_data):
        assessment_id = agent_status_data["assessment"]["id"]
        data = get(f"/assessments/{assessment_id}/agent-status")
        assert isinstance(data, list), (
            f"GET /assessments/{assessment_id}/agent-status must return a list, got {type(data)}"
        )

    def test_agent_status_contains_created_tasks(self, agent_status_data):
        assessment_id = agent_status_data["assessment"]["id"]
        data = get(f"/assessments/{assessment_id}/agent-status")
        workstreams = [item.get("workstream") for item in data]
        assert "kubernetes" in workstreams, (
            f"Expected 'kubernetes' in workstreams, got {workstreams}"
        )
        assert "cloud_strategy" in workstreams, (
            f"Expected 'cloud_strategy' in workstreams, got {workstreams}"
        )

    def test_agent_status_item_shape(self, agent_status_data):
        assessment_id = agent_status_data["assessment"]["id"]
        data = get(f"/assessments/{assessment_id}/agent-status")
        assert len(data) >= 1, "agent-status must return at least one item"
        first = data[0]
        for key in ("task_id", "workstream", "agent_type", "status"):
            assert key in first, f"Missing key '{key}' in agent-status item: {first}"

    def test_agent_status_reflects_task_status(self, agent_status_data):
        assessment_id = agent_status_data["assessment"]["id"]
        data = get(f"/assessments/{assessment_id}/agent-status")
        kubernetes_items = [item for item in data if item.get("workstream") == "kubernetes"]
        assert len(kubernetes_items) >= 1, (
            "Expected at least one 'kubernetes' item in agent-status"
        )
        assert kubernetes_items[0].get("status") == "in_progress", (
            f"kubernetes task status must be 'in_progress', got '{kubernetes_items[0].get('status')}'"
        )

    def test_agent_status_unknown_assessment(self, agent_status_data):
        fake_id = str(uuid.uuid4())
        r = requests.get(api(f"/assessments/{fake_id}/agent-status"), timeout=15)
        assert r.status_code == 404, (
            f"Expected HTTP 404 for unknown assessment, got {r.status_code}: {r.text[:300]}"
        )

    def test_question_approval_status_persists_after_list(self, agent_status_data):
        """Create a new interview, suggest a question, approve it, then verify via list."""
        suffix = uuid.uuid4().hex[:6]
        assessment = post("/assessments", {
            "client_name": "Migros-S10-Persist",
            "project_name": f"Sprint10-Persist-{suffix}",
        })
        task = post("/tasks", {
            "assessment_id": assessment["id"],
            "agent_type": "kubernetes",
            "workstream": "kubernetes",
            "status": "in_progress",
        })
        interview = post("/interviews", {
            "task_id": task["id"],
            "interviewee_name": "PersistenceTestConsultant",
        })
        # Add an initial question
        post(f"/interviews/{interview['id']}/questions", {
            "interview_id": interview["id"],
            "text": "Baseline question for persistence test",
            "order": 1,
            "agent_suggested": False,
        })
        # Suggest a follow-up
        r = requests.post(
            api(f"/interviews/{interview['id']}/suggest-followup"),
            json={},
            timeout=15,
        )
        assert r.status_code == 201, (
            f"suggest-followup → {r.status_code}: {r.text[:300]}"
        )
        suggestion_id = r.json()["id"]

        # Approve the suggestion
        patch(f"/interviews/questions/{suggestion_id}/approval", json={"action": "approved"})

        # Verify the approved status persists in the question list
        questions = get(f"/interviews/{interview['id']}/questions")
        approved = [q for q in questions if q.get("id") == suggestion_id]
        assert len(approved) == 1, f"Approved question {suggestion_id} not found in list"
        assert approved[0].get("approval_status") == "approved", (
            f"approval_status must remain 'approved' after listing, "
            f"got '{approved[0].get('approval_status')}'"
        )
