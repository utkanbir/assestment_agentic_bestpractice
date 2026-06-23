"""
Sprint 18 API checks:
- report compose + PATCH content_json
- ai-edit endpoint
- export pdf/docx
- chat messages GET + session detail
"""
import json
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=90)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def patch(path, json=None, expected=200):
    r = requests.patch(api(path), json=json or {}, timeout=30)
    assert r.status_code == expected, f"PATCH {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def sprint18_setup():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S18",
        "project_name": f"Sprint18-{suffix}",
        "description": "Sprint18 integration test",
    })
    task = post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S18 test",
        "status": "in_progress",
    })
    return {"assessment_id": assessment["id"], "task_id": task["id"]}


def test_compose_report_content_json(sprint18_setup):
    report = post(
        f"/reports/assessment/{sprint18_setup['assessment_id']}/compose",
        expected=200,
    )
    assert report["assessment_id"] == sprint18_setup["assessment_id"]
    assert report.get("content_json")
    content = json.loads(report["content_json"])
    assert content.get("version") == 1
    assert len(content.get("sections", [])) >= 5
    section_types = {s["type"] for s in content["sections"]}
    assert "cover" in section_types
    assert "text" in section_types


def test_patch_report_content(sprint18_setup):
    reports = get("/reports", params={"assessment_id": sprint18_setup["assessment_id"]})
    assert reports
    report_id = reports[0]["id"]
    content = json.loads(reports[0]["content_json"])
    for s in content["sections"]:
        if s.get("id") == "notes":
            s["body"] = "Danisman notu test"
    updated = patch(f"/reports/{report_id}", {"content_json": json.dumps(content, ensure_ascii=False)})
    parsed = json.loads(updated["content_json"])
    notes = next(s for s in parsed["sections"] if s.get("id") == "notes")
    assert notes["body"] == "Danisman notu test"


def test_ai_edit_report_section(sprint18_setup):
    reports = get("/reports", params={"assessment_id": sprint18_setup["assessment_id"]})
    report_id = reports[0]["id"]
    result = post(
        f"/reports/{report_id}/ai-edit",
        json={"section_id": "notes", "instruction": "Kısa tut", "mode": "shorten"},
        expected=200,
    )
    assert "notes" in result["updated_sections"]
    assert result.get("content_json")


def test_export_pdf_and_docx(sprint18_setup):
    reports = get("/reports", params={"assessment_id": sprint18_setup["assessment_id"]})
    report_id = reports[0]["id"]
    pdf = requests.post(api(f"/reports/{report_id}/export/pdf?force=true"), timeout=60)
    assert pdf.status_code == 200, pdf.text[:200]
    assert len(pdf.content) > 100
    docx = requests.post(api(f"/reports/{report_id}/export/docx?force=true"), timeout=60)
    assert docx.status_code == 200, docx.text[:200]
    assert docx.headers.get("content-type", "").startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_chat_session_messages_and_multiturn(sprint18_setup):
    session = post("/chat/sessions", {
        "assessment_id": sprint18_setup["assessment_id"],
        "workstream": "kubernetes",
        "title": "S18 test chat",
    })
    session_id = session["id"]

    detail = get(f"/chat/sessions/{session_id}")
    assert detail["title"] == "S18 test chat"

    post(f"/chat/sessions/{session_id}/messages", {"content": "Merhaba, kubernetes durumu?"}, expected=200)
    post(f"/chat/sessions/{session_id}/messages", {"content": "Önceki mesaja devam et"}, expected=200)

    messages = get(f"/chat/sessions/{session_id}/messages")
    assert len(messages) >= 4
    roles = [m["role"] for m in messages]
    assert "user" in roles and "assistant" in roles

    patched = patch(f"/chat/sessions/{session_id}", {"title": "Güncel başlık"})
    assert patched["title"] == "Güncel başlık"
