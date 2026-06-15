# S5-AA-007: Human review interrupt for research-agent candidate knowledge
from agent.state import ResearchAgentState


async def human_review(state: ResearchAgentState) -> dict:
    decision = state.get("reviewer_decision")
    if decision == "approved":
        return {"status": "approved"}
    elif decision == "rejected":
        return {"status": "rejected"}
    return {"status": "pending"}
