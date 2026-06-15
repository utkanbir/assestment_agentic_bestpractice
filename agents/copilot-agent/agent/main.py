# S5-AA-004/005: Co-Pilot Agent FastAPI entry point
import uuid
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from agent.graph import build_graph

log = logging.getLogger(__name__)
app = FastAPI(title="AAKP Ontology Co-Pilot Agent")
checkpointer = MemorySaver()
graph = build_graph(checkpointer)


class ProposalRequest(BaseModel):
    proposal_text: str
    submitted_by: str = "consultant"


class ReviewDecision(BaseModel):
    decision: str   # "approved" | "rejected"
    reviewer_note: str | None = None


@app.post("/proposals", status_code=202)
async def submit_proposal(body: ProposalRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    await graph.ainvoke(
        {"proposal_text": body.proposal_text, "submitted_by": body.submitted_by},
        config=config,
    )
    state = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "status": state.values.get("status", "pending"),
        "candidate_triples": state.values.get("candidate_triples", []),
        "validation_errors": state.values.get("validation_errors", []),
        "human_review_required": state.values.get("human_review_required", True),
    }


@app.patch("/proposals/{thread_id}/review")
async def review_proposal(thread_id: str, body: ReviewDecision):
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state:
        raise HTTPException(status_code=404, detail="Proposal not found")
    await graph.aupdate_state(
        config,
        {"reviewer_decision": body.decision, "reviewer_note": body.reviewer_note},
    )
    await graph.ainvoke(None, config=config)
    final_state = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "status": final_state.values.get("status"),
        "published_uri": final_state.values.get("published_uri"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
