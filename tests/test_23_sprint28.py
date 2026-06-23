"""
Sprint 28 API tests:
- expertise catalog endpoint
- multi-expertise consultant create
- create does not auto-assign
- assessment assign/unassign
- answer PATCH consultant fields
- answer consultant-review (AI kontrol)
"""
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


def patch(path, json=None, expected=200):
    r = requests.patch(api(path), json=json or {}, timeout=30)
    assert r.status_code == expected, f"PATCH {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def delete(path, expected=204):
    r = requests.delete(api(path), timeout=30)
    assert r.status_code == expected, f"DELETE {path} -> {r.status_code}: {r.text[:300]}"


def test_expertise_catalog():
    catalog = get("/consultants/expertise-catalog")
    assert catalog["groups"]
    tags = [t for g in catalog["groups"] for t in g["tags"]]
    assert "Snowflake" in tags
    assert "LLM" in tags


def test_create_consultant_multi_expertise():
    suffix = uuid.uuid4().hex[:6]
    created = post("/consultants", {
        "first_name": "S28",
        "last_name": f"Expert-{suffix}",
        "role": "Data Architect",
        "expertise": ["Snowflake", "LLM", "AWS"],
    })
    assert set(created["expertise"]) == {"Snowflake", "LLM", "AWS"}


def test_create_no_auto_assign():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "S28-NoAssign",
        "project_name": f"NA-{suffix}",
    })
    consultant = post("/consultants", {
        "first_name": "Pool",
        "last_name": f"Only-{suffix}",
        "expertise": ["Oracle"],
    })
    assigned = get(f"/assessments/{assessment['id']}/consultants")
    assert not any(c["id"] == consultant["id"] for c in assigned)


def test_assessment_assign_consultant():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "S28-Assign",
        "project_name": f"As-{suffix}",
    })
    consultant = post("/consultants", {
        "first_name": "Assign",
        "last_name": f"Test-{suffix}",
        "expertise": ["Databricks"],
    })
    post(f"/assessments/{assessment['id']}/consultants", {"consultant_id": consultant["id"]}, expected=201)
    listed = get(f"/assessments/{assessment['id']}/consultants")
    assert any(c["id"] == consultant["id"] for c in listed)
    delete(f"/assessments/{assessment['id']}/consultants/{consultant['id']}")
    listed2 = get(f"/assessments/{assessment['id']}/consultants")
    assert not any(c["id"] == consultant["id"] for c in listed2)


def test_answer_consultant_patch():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {"client_name": "S28-Patch", "project_name": f"P-{suffix}"})
    consultant = post("/consultants", {
        "first_name": "Patch",
        "last_name": "Consultant",
        "expertise": ["LLM"],
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "Lead"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "DR stratejiniz?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "Multi-AZ ve yedekleme var.",
    })
    updated = patch(f"/interviews/answers/{answer['id']}", {
        "consultant_id": consultant["id"],
        "consultant_comment": "RPO hedefi netleştirilmeli.",
    })
    assert updated["consultant_id"] == consultant["id"]
    assert "RPO" in (updated["consultant_comment"] or "")
    assert len(updated.get("consultant_comments") or []) == 1
    assert updated["consultant_comments"][0]["consultant_id"] == consultant["id"]


def test_multi_consultant_comments_per_answer():
    suffix = uuid.uuid4().hex[:6]
    task = post("/tasks", {
        "assessment_id": post("/assessments", {
            "client_name": "S29-Multi",
            "project_name": f"M-{suffix}",
        })["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "status": "in_progress",
    })
    c1 = post("/consultants", {"first_name": "Ali", "last_name": f"A-{suffix}", "expertise": ["AWS"]})
    c2 = post("/consultants", {"first_name": "Ayşe", "last_name": f"B-{suffix}", "expertise": ["Snowflake"]})
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "Lead"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Veri platformu?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "Lakehouse kullanıyoruz.",
    })
    cc1 = post(f"/interviews/answers/{answer['id']}/consultant-comments", {
        "consultant_id": c1["id"],
        "comment": "AWS maliyet optimizasyonu önerilir.",
    })
    cc2 = post(f"/interviews/answers/{answer['id']}/consultant-comments", {
        "consultant_id": c2["id"],
        "comment": "Snowflake entegrasyonu değerlendirilmeli.",
    })
    assert cc1["consultant_id"] == c1["id"]
    assert cc2["consultant_id"] == c2["id"]
    listed = get(f"/interviews/questions/{question['id']}/answers")
    assert len(listed) == 1
    comments = listed[0].get("consultant_comments") or []
    assert len(comments) == 2
    ids = {c["consultant_id"] for c in comments}
    assert c1["id"] in ids and c2["id"] in ids
    review = post(
        f"/interviews/answers/{answer['id']}/consultant-comments/{cc1['id']}/consultant-review",
        {},
        expected=200,
    )
    assert "feedback" in review
    updated = patch(
        f"/interviews/answers/{answer['id']}/consultant-comments/{cc2['id']}",
        {"comment": "Snowflake POC planlanmalı."},
    )
    assert "POC" in (updated["comment"] or "")


def test_answer_consultant_review():
    suffix = uuid.uuid4().hex[:6]
    task = post("/tasks", {
        "assessment_id": post("/assessments", {
            "client_name": "S28-Review",
            "project_name": f"R-{suffix}",
        })["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "Ops"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Güvenlik politikaları?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "Network policy ve RBAC uygulanıyor.",
        "consultant_comment": "Zero trust ile uyumlu bir yaklaşım.",
    })
    review = post(f"/interviews/answers/{answer['id']}/consultant-review", {}, expected=200)
    assert "feedback" in review
    assert isinstance(review["consistent"], bool)


def test_mock_consultant_review_flags_unprofessional_comment():
    """Mock AI kontrol should not approve offensive consultant tone."""
    suffix = uuid.uuid4().hex[:6]
    task = post("/tasks", {
        "assessment_id": post("/assessments", {
            "client_name": "S28-ReviewBad",
            "project_name": f"RB-{suffix}",
        })["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "Ops"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "K8s mimarisi?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "bilmiyorum",
        "consultant_comment": "o zaman ne bok yemeye geldin karsima sk kafali",
    })
    review = post(f"/interviews/answers/{answer['id']}/consultant-review", {}, expected=200)
    assert review["consistent"] is False
    assert "profesyonel değil" in review["feedback"].lower()


def test_mock_evaluate_answer_vague_response():
    """With mock-local-dev API key, evaluate still returns useful text (not error)."""
    suffix = uuid.uuid4().hex[:6]
    task = post("/tasks", {
        "assessment_id": post("/assessments", {
            "client_name": "S28-MockEval",
            "project_name": f"ME-{suffix}",
        })["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "status": "in_progress",
    })
    interview = post("/interviews", {"task_id": task["id"], "interviewee_name": "Ops"})
    question = post(f"/interviews/{interview['id']}/questions", {
        "interview_id": interview["id"],
        "text": "Cluster mimariniz?",
        "order": 1,
    })
    answer = post(f"/interviews/questions/{question['id']}/answers", {
        "question_id": question["id"],
        "text": "bilmiyorum",
    })
    ev = post(f"/interviews/answers/{answer['id']}/evaluate", expected=200)
    assert ev["evaluation"]
    assert "Değerlendirme sırasında hata" not in ev["evaluation"]
    assert "Başlangıç" in ev["evaluation"] or "yerel" in ev["evaluation"].lower()
