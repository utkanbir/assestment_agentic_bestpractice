# S4-AA-001: Orchestrator Agent LangGraph graph (Supervisor pattern)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.state import OrchestratorState
from agent.nodes import (
    task_monitor,
    dependency_checker,
    conflict_detector,
    risk_consolidator,
    rule6_propagator,
    executive_summary_gen,
    roadmap_generator,
)
from agent.config import settings


def _should_wait_for_human(state: OrchestratorState) -> str:
    """Route: if conflicts found → interrupt for human review, else continue."""
    return "human_review" if state.human_review_required else "risk_consolidator"


def build_graph(checkpointer=None):
    g = StateGraph(OrchestratorState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    g.add_node("task_monitor",        task_monitor)        # S4-AA-002
    g.add_node("rule6_propagator",    rule6_propagator)    # S4-KA-001
    g.add_node("dependency_checker",  dependency_checker)  # S4-AA-003
    g.add_node("conflict_detector",   conflict_detector)   # S4-AA-004
    g.add_node("human_review",        lambda s: s)         # interrupt point
    g.add_node("risk_consolidator",   risk_consolidator)   # S4-AA-005
    g.add_node("executive_summary_gen", executive_summary_gen)  # S4-AA-006
    g.add_node("roadmap_generator",   roadmap_generator)   # S4-AA-007

    # ── Edges ────────────────────────────────────────────────────────────────
    g.set_entry_point("task_monitor")
    g.add_edge("task_monitor",       "rule6_propagator")
    g.add_edge("rule6_propagator",   "dependency_checker")
    g.add_edge("dependency_checker", "conflict_detector")

    # Conditional: conflicts → human review first
    g.add_conditional_edges(
        "conflict_detector",
        _should_wait_for_human,
        {
            "human_review":    "human_review",
            "risk_consolidator": "risk_consolidator",
        },
    )
    g.add_edge("human_review",       "risk_consolidator")  # resumes after approval

    g.add_edge("risk_consolidator",     "executive_summary_gen")
    g.add_edge("executive_summary_gen", "roadmap_generator")
    g.add_edge("roadmap_generator",     END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],
    )


async def create_graph():
    from psycopg_pool import AsyncConnectionPool
    pool = AsyncConnectionPool(conninfo=settings.postgres_url, open=False)
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return build_graph(checkpointer=checkpointer)
