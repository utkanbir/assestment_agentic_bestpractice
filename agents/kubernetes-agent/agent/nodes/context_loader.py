from agent.config import settings
from agent.state import KubernetesAgentState
import httpx


async def context_loader(state: KubernetesAgentState) -> dict:
    task_id = state["task_id"]

    async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=30) as client:
        task_resp = await client.get(f"/api/v1/tasks/{task_id}")
        task_resp.raise_for_status()
        task = task_resp.json()

        findings_resp = await client.get(f"/api/v1/knowledge/tasks/{task_id}/findings")
        existing_findings = findings_resp.json() if findings_resp.status_code == 200 else []

    scope = task.get("scope") or f"Kubernetes Assessment — {task.get('workstream', 'K8s')}"

    return {
        "task_scope": scope,
        "existing_findings": existing_findings,
        "covered_areas": [f.get("area", "") for f in existing_findings if isinstance(f, dict)],
        "phase": "INTERVIEW_LOOP",
        "answer_count": 0,
        "pending_evidence": [],
        "pending_findings": [],
        "approved_finding_ids": [],
        "should_end_interview": False,
        "human_approval_required": False,
    }
