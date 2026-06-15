# S5-AA-006/007: Research Agent FastAPI entry point
import uuid
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from agent.graph import build_graph

log = logging.getLogger(__name__)
app = FastAPI(title="AAKP Domain Research Agent")
checkpointer = MemorySaver()
graph = build_graph(checkpointer)


class ResearchRequest(BaseModel):
    topic: str
    domain: str = "data_governance"
    submitted_by: str = "consultant"


class ReviewDecision(BaseModel):
    decision: str   # "approved" | "rejected"
    reviewer_note: str | None = None


@app.post("/research", status_code=202)
async def start_research(body: ResearchRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    await graph.ainvoke(
        {"topic": body.topic, "domain": body.domain, "submitted_by": body.submitted_by},
        config=config,
    )
    state = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "status": state.values.get("status"),
        "synthesized_summary": state.values.get("synthesized_summary", ""),
        "candidate_triples": state.values.get("candidate_triples", []),
        "human_review_required": state.values.get("human_review_required", True),
    }


@app.patch("/research/{thread_id}/review")
async def review_research(thread_id: str, body: ReviewDecision):
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state:
        raise HTTPException(status_code=404, detail="Research thread not found")
    await graph.aupdate_state(
        config,
        {"reviewer_decision": body.decision, "reviewer_note": body.reviewer_note},
    )
    await graph.ainvoke(None, config=config)
    final = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "status": final.values.get("status"),
        "published_uri": final.values.get("published_uri"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
