from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.config import settings
from agent.state import WorkstreamAgentState
from agent.nodes import (
    answer_processor,
    confidence_propagator,
    context_loader,
    evidence_capture,
    finding_detector,
    kg_writer,
    question_advisor,
    report_generator,
    risk_reasoner,
    similar_findings_fetcher,
)


def _route_after_evidence(state: WorkstreamAgentState) -> str:
    # S5-AA-001: finding node only reachable when evidence has been captured
    if state.get("evidence_captured"):
        return "similar_findings_fetcher"
    if state.get("answer_count", 0) >= 8:
        return "kg_writer"
    return "question_advisor"


def _route_after_finding(state: WorkstreamAgentState) -> str:
    # S5-AA-002: risk node only reachable when at least one finding exists
    if state.get("should_end_interview"):
        if state.get("finding_ids"):
            return "kg_writer"
        return "report_generator"  # no findings → skip risk reasoning
    return "question_advisor"


def _route_after_kg(state: WorkstreamAgentState) -> str:
    if state.get("approved_finding_ids"):
        return "risk_reasoner"
    return "report_generator"


def _route_after_risk(state: WorkstreamAgentState) -> str:
    # S5-AA-003: report only generated after validation flag is set
    if state.get("risks_validated"):
        return "confidence_propagator"
    return "report_generator"  # skip confidence propagation if no validated risks


def build_graph(checkpointer):
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    builder = StateGraph(WorkstreamAgentState)

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

    builder.set_entry_point("context_loader")
    builder.add_edge("context_loader", "question_advisor")
    builder.add_edge("question_advisor", "answer_processor")
    builder.add_edge("answer_processor", "evidence_capture")

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
    builder.add_conditional_edges(
        "risk_reasoner",
        _route_after_risk,
        {"confidence_propagator": "confidence_propagator", "report_generator": "report_generator"},
    )
    builder.add_edge("confidence_propagator", "report_generator")
    builder.add_edge("report_generator", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["answer_processor"],
    )
