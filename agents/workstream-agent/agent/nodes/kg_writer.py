import httpx

from agent.config import settings
from agent.state import WorkstreamAgentState


async def kg_writer(state: WorkstreamAgentState) -> dict:
    task_id = state["task_id"]
    interview_id = state.get("interview_id")
    written_finding_ids = []

    async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=30) as client:
        for i, evidence_data in enumerate(state.get("pending_evidence", [])):
            ev_resp = await client.post("/api/v1/evidences", json={
                "source": evidence_data.get("source", "interview"),
                "content": evidence_data["content"],
                "evidence_type": evidence_data.get("evidence_type", "interview"),
                "interview_id": interview_id,
            })
            if ev_resp.status_code != 201:
                continue
            evidence = ev_resp.json()

            for finding in state.get("pending_findings", []):
                if finding.get("evidence_index") == i:
                    if state.get("human_approval_required") and finding["severity"] in ("critical", "high"):
                        if finding.get("description") not in state.get("approved_finding_ids", []):
                            continue
                    f_resp = await client.post("/api/v1/findings", json={
                        "task_id": task_id,
                        "evidence_id": evidence["id"],
                        "description": finding["description"],
                        "severity": finding["severity"],
                        "confidence": finding["confidence"],
                    })
                    if f_resp.status_code == 201:
                        written_finding_ids.append(f_resp.json()["id"])

        await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed"})

    return {
        "approved_finding_ids": written_finding_ids,
        "phase": "POST_INTERVIEW",
    }
