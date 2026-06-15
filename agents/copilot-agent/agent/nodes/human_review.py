# S5-AA-005: Human review node — LangGraph interrupt point
# Reviewer calls PATCH /api/v1/approvals/candidates/{id} to set decision
from agent.state import CopilotState


async def human_review(state: CopilotState) -> dict:
    # This node is an interrupt point (interrupt_before=["human_review"])
    # The graph resumes when the reviewer posts their decision via the API
    decision = state.get("reviewer_decision")
    if decision == "approved":
        return {"status": "approved"}
    elif decision == "rejected":
        return {"status": "rejected"}
    # If resumed without a decision, keep pending (should not happen)
    return {"status": "pending"}
