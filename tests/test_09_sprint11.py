"""
S11-TA-001: Sprint 11 E2E — Answer evaluation, agent metrics, document upload, question suggest

Run:
    $env:API_BASE = "http://localhost:8000/api/v1"
    py -m pytest tests/test_09_sprint11.py -v
"""
import io
import uuid

import pytest
import requests

from conftest import API_BASE

EXPECTED_WORKSTREAMS = [
    "kubernetes",
    "cloud_strategy",
    "ingestion",
    "teradata_dr",
    "lakehouse",
    "governance",
    "data_product",
    "cdp",
]


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


# ─── Sınıf 1: Answer evaluation ──────────────────────────────────────────────

@pytest.fixture(scope="class")
def evaluate_flow_data():
    """Create assessment → task → interview → question → answer for evaluate tests."""
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S11-Evaluate",
        "project_name": f"Sprint11-Evaluate-{suffix}",
        "description": "Sprint 11 E2E — answer evaluation endpoint",
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
        "interviewee_name": "EvaluateTestConsultant",
    })
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Kubernetes RBAC yapılandırmanızı nasıl yönetiyorsunuz?",
        "order": 1,
        "agent_suggested": False,
    })
    answer = post(
        f"/interviews/questions/{question['id']}/answers",
        {
            "question_id": question["id"],
            "text": (
                "ClusterRole ve RoleBinding kullanıyoruz. "
                "Production namespace'lerinde least-privilege prensibi uygulanıyor."
            ),
        },
    )
    return {
        "assessment": assessment,
        "task": task,
        "interview": interview,
        "question": question,
        "answer": answer,
    }


@pytest.mark.usefixtures("evaluate_flow_data")
class TestEvaluateAnswer:
    """S11-TA-001: POST /interviews/answers/{id}/evaluate."""

    def test_evaluate_answer_returns_non_empty_evaluation(self, evaluate_flow_data):
        answer_id = evaluate_flow_data["answer"]["id"]
        r = requests.post(api(f"/interviews/answers/{answer_id}/evaluate"), json={}, timeout=60)
        assert r.status_code == 200, (
            f"POST /interviews/answers/{answer_id}/evaluate → {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert data.get("answer_id") == answer_id, (
            f"answer_id must match request, got {data.get('answer_id')}"
        )
        evaluation = data.get("evaluation")
        assert isinstance(evaluation, str) and len(evaluation) > 0, (
            f"evaluation must be a non-empty string, got {evaluation!r}"
        )

    def test_evaluate_nonexistent_answer_returns_404(self, evaluate_flow_data):
        fake_id = str(uuid.uuid4())
        r = requests.post(api(f"/interviews/answers/{fake_id}/evaluate"), json={}, timeout=15)
        assert r.status_code == 404, (
            f"Expected HTTP 404 for unknown answer, got {r.status_code}: {r.text[:300]}"
        )


# ─── Sınıf 2: Agent metrics ──────────────────────────────────────────────────

class TestAgentMetrics:
    """S11-TA-001: GET /agents/metrics and /agents/metrics/{workstream}."""

    def test_metrics_returns_eight_workstreams(self):
        data = get("/agents/metrics")
        assert isinstance(data, list), f"GET /agents/metrics must return a list, got {type(data)}"
        assert len(data) == 8, f"Expected 8 workstream metrics, got {len(data)}"
        workstreams = [item.get("workstream") for item in data]
        assert workstreams == EXPECTED_WORKSTREAMS, (
            f"Unexpected workstream order or names: {workstreams}"
        )

    def test_metrics_item_shape(self):
        data = get("/agents/metrics")
        assert len(data) >= 1, "metrics list must not be empty"
        first = data[0]
        for key in (
            "workstream",
            "interviews_conducted",
            "questions_total",
            "questions_agent_suggested",
            "suggestions_approved",
            "suggestions_rejected",
            "suggestions_pending",
            "answers_total",
            "answers_evaluated",
            "documents_loaded",
        ):
            assert key in first, f"Missing key '{key}' in metrics item: {first}"

    def test_kubernetes_workstream_metrics(self):
        data = get("/agents/metrics/kubernetes")
        assert isinstance(data, dict), (
            f"GET /agents/metrics/kubernetes must return an object, got {type(data)}"
        )
        assert data.get("workstream") == "kubernetes", (
            f"workstream must be 'kubernetes', got {data.get('workstream')}"
        )


# ─── Sınıf 3: Knowledge document upload ──────────────────────────────────────

class TestKnowledgeDocumentUpload:
    """S11-TA-001: POST /agents/{workstream}/documents."""

    def test_upload_text_document(self):
        filename = f"sprint11-test-{uuid.uuid4().hex[:8]}.txt"
        content = b"Kubernetes RBAC best practices and namespace isolation guidelines."
        files = {"file": (filename, io.BytesIO(content), "text/plain")}
        r = requests.post(api("/agents/kubernetes/documents"), files=files, timeout=30)
        assert r.status_code == 201, (
            f"POST /agents/kubernetes/documents → {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert data.get("filename") == filename, (
            f"filename must match upload, got {data.get('filename')}"
        )
        assert data.get("workstream") == "kubernetes", (
            f"workstream must be 'kubernetes', got {data.get('workstream')}"
        )
        assert "id" in data, "Response must contain 'id'"
        assert "chunk_count" in data, "Response must contain 'chunk_count'"


# ─── Sınıf 4: Question bank suggest ──────────────────────────────────────────

class TestQuestionBankSuggest:
    """S11-TA-001: POST /question-bank/suggest."""

    def test_suggest_questions_returns_list(self):
        r = requests.post(
            api("/question-bank/suggest"),
            json={"workstream": "kubernetes", "count": 3},
            timeout=30,
        )
        assert r.status_code == 200, (
            f"POST /question-bank/suggest → {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert isinstance(data, list), (
            f"suggest must return a list (may be empty without API key), got {type(data)}"
        )
        for item in data:
            assert isinstance(item, dict), f"Each suggestion must be an object, got {item!r}"
            assert "text" in item, f"Each suggestion must have 'text' key: {item}"
            assert isinstance(item["text"], str), (
                f"suggestion text must be a string, got {type(item['text'])}"
            )
