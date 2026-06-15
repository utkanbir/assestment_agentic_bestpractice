# S4-AA-002: Task monitor — hangi task'lar complete?
import httpx
from agent.config import settings
from agent.state import OrchestratorState


async def task_monitor(state: OrchestratorState) -> dict:
    async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=30) as client:
        resp = await client.get(f"/api/v1/tasks?assessment_id={state.assessment_id}")
        tasks = resp.json() if resp.status_code == 200 else []

    completed = [t["id"] for t in tasks if t.get("status") == "completed"]
    pending = [t["id"] for t in tasks if t.get("status") != "completed"]

    return {
        "all_tasks": tasks,
        "completed_tasks": completed,
        "pending_tasks": pending,
    }
