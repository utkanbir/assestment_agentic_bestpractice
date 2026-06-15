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
    finding_detector,
    kg_writer,
    report_generator,
)


def _route_after_finding(state: KubernetesAgentState) -> str:
    if state.get("should_end_interview"):
        return "kg_writer"
    return "question_advisor"


def _route_after_kg(state: KubernetesAgentState) -> str:
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
    builder.add_node("finding_detector", partial(finding_detector, llm=llm))
    builder.add_node("kg_writer", kg_writer)
    builder.add_node("report_generator", partial(report_generator, llm=llm))

    # Edges
    builder.set_entry_point("context_loader")
    builder.add_edge("context_loader", "question_advisor")

    # After question_advisor, graph pauses for human input (interrupt_before=["answer_processor"])
    builder.add_edge("question_advisor", "answer_processor")
    builder.add_edge("answer_processor", "evidence_capture")
    builder.add_edge("evidence_capture", "finding_detector")

    builder.add_conditional_edges(
        "finding_detector",
        _route_after_finding,
        {"kg_writer": "kg_writer", "question_advisor": "question_advisor"},
    )

    builder.add_edge("kg_writer", "report_generator")
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
