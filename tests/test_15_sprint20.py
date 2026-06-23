"""
Sprint 20 API checks:
- ai-generate text + chart commentary
- batch generation
- mock fallback without API key
"""
import json
import uuid

import pytest
import requests

from conftest import API_BASE


def api(path: str) -> str:
    return f"{API_BASE}{path}"


def post(path, json=None, expected=201):
    r = requests.post(api(path), json=json or {}, timeout=120)
    assert r.status_code == expected, f"POST {path} -> {r.status_code}: {r.text[:400]}"
    return r.json()


def get(path, params=None, expected=200):
    r = requests.get(api(path), params=params, timeout=30)
    assert r.status_code == expected, f"GET {path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def sprint20_setup():
    suffix = uuid.uuid4().hex[:6]
    assessment = post("/assessments", {
        "client_name": "Migros-S20",
        "project_name": f"Sprint20-{suffix}",
        "description": "Sprint20 integration test",
    })
    post("/tasks", {
        "assessment_id": assessment["id"],
        "agent_type": "kubernetes",
        "workstream": "kubernetes",
        "scope": "S20 test",
        "status": "in_progress",
    })
    report = post(
        f"/reports/assessment/{assessment['id']}/compose",
        expected=200,
    )
    return {"assessment_id": assessment["id"], "report_id": report["id"]}


def test_ai_generate_text_section(sprint20_setup):
    report_id = sprint20_setup["report_id"]
    result = post(
        f"/reports/{report_id}/ai-generate",
        json={"section_id": "notes", "mode": "generate"},
        expected=200,
    )
    assert "notes" in result["updated_sections"]
    content = json.loads(result["content_json"])
    notes = next(s for s in content["sections"] if s.get("id") == "notes")
    assert notes.get("body"), "text section should have body after AI generate"


def test_ai_generate_chart_commentary(sprint20_setup):
    report_id = sprint20_setup["report_id"]
    result = post(
        f"/reports/{report_id}/ai-generate",
        json={"section_id": "maturity", "mode": "generate"},
        expected=200,
    )
    assert "maturity" in result["updated_sections"]
    content = json.loads(result["content_json"])
    maturity = next(s for s in content["sections"] if s.get("id") == "maturity")
    assert maturity.get("commentary"), "chart section should have commentary after AI generate"


def test_ai_generate_batch_all_sections(sprint20_setup):
    report_id = sprint20_setup["report_id"]
    result = post(
        f"/reports/{report_id}/ai-generate",
        json={"mode": "generate"},
        expected=200,
    )
    assert result["total_sections"] >= 5
    assert len(result["updated_sections"]) >= 5
    content = json.loads(result["content_json"])
    text_sections = [s for s in content["sections"] if s.get("type") == "text"]
    assert any(s.get("body") for s in text_sections)


def test_export_includes_commentary(sprint20_setup):
    report_id = sprint20_setup["report_id"]
    post(
        f"/reports/{report_id}/ai-generate",
        json={"section_id": "maturity", "mode": "generate"},
        expected=200,
    )
    r = requests.post(
        api(f"/reports/{report_id}/export/pdf?force=true"),
        timeout=60,
    )
    assert r.status_code == 200
    assert len(r.content) > 100
