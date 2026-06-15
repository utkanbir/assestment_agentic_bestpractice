from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.config import settings
from agent.state import KubernetesAgentState
from agent.nodes import (
    context_loader,
    answer_processor,
    question_advisor,
    evidence_capture,
    similar_findings_fetcher,
    finding_detector,
    kg_writer,
    risk_reasoner,
    confidence_propagator,
    report_generator,
)


def _route_after_evidence(state: KubernetesAgentState) -> str:
    """S2-AA-003: skip finding_detector when no evidence was captured.
    S2-AA-005: route through similar_findings_fetcher before finding_detector."""
    if state.get("evidence_captured"):
        return "similar_findings_fetcher"
    if state.get("answer_count", 0) >= 8:
        return "kg_writer"
    return "question_advisor"


def _route_after_finding(state: KubernetesAgentState) -> str:
    if state.get("should_end_interview"):
        return "kg_writer"
    return "question_advisor"


def _route_after_kg(state: KubernetesAgentState) -> str:
    # Only run risk_reasoner when there are approved findings to process
    if state.get("approved_finding_ids"):
        return "risk_reasoner"
    return "report_generator"


def build_graph(checkpointer):
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    builder = StateGraph(KubernetesAgentState)

    # Bind LLM into nodes that need it
    builder.add_node("context_loader", context_loader)
    builder.add_node("question_advisor", partial(question_advisor, llm=llm))
    builder.add_node("answer_processor", answer_processor)
    builder.add_node("evidence_capture", partial(evidence_capture, llm=llm))
    builder.add_node("similar_findings_fetcher", similar_findings_fetcher)
    builder.add_node("finding_detector", partial(finding_detector, llm=llm))
    builder.add_node("kg_writer", kg_writer)
    builder.add_node("risk_reasoner", partial(risk_reasoner, llm=llm))
    builder.add_node("confidence_propagator", confidence_propagator)
    builder.add_node("report_generator", partial(report_generator, llm=llm))

    # Edges
    builder.set_entry_point("context_loader")
    builder.add_edge("context_loader", "question_advisor")

    # After question_advisor, graph pauses for human input (interrupt_before=["answer_processor"])
    builder.add_edge("question_advisor", "answer_processor")
    builder.add_edge("answer_processor", "evidence_capture")

    # S2-AA-003: guard — only enter similar_findings_fetcher if evidence was captured
    # S2-AA-005: similar_findings_fetcher always leads to finding_detector
    builder.add_conditional_edges(
        "evidence_capture",
        _route_after_evidence,
        {
            "similar_findings_fetcher": "similar_findings_fetcher",
            "question_advisor": "question_advisor",
            "kg_writer": "kg_writer",
        },
    )
    builder.add_edge("similar_findings_fetcher", "finding_detector")

    builder.add_conditional_edges(
        "finding_detector",
        _route_after_finding,
        {"kg_writer": "kg_writer", "question_advisor": "question_advisor"},
    )

    builder.add_conditional_edges(
        "kg_writer",
        _route_after_kg,
        {"risk_reasoner": "risk_reasoner", "report_generator": "report_generator"},
    )
    builder.add_edge("risk_reasoner", "confidence_propagator")
    builder.add_edge("confidence_propagator", "report_generator")
    builder.add_edge("report_generator", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["answer_processor"],
    )


async def get_graph():
    """Return compiled graph with PostgreSQL checkpointer."""
    async with AsyncPostgresSaver.from_conn_string(settings.postgres_url) as checkpointer:
        await checkpointer.setup()
        return build_graph(checkpointer)
