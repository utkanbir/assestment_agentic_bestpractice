# S5-AA-006/007: Domain Research Agent graph
from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from agent.config import settings
from agent.state import ResearchAgentState
from agent.nodes.web_researcher import web_researcher
from agent.nodes.knowledge_synthesizer import knowledge_synthesizer
from agent.nodes.candidate_writer import candidate_writer
from agent.nodes.human_review import human_review
from agent.nodes.knowledge_promoter import knowledge_promoter


def _route_after_synthesis(state: ResearchAgentState) -> str:
    if state.get("status") == "failed":
        return END
    return "candidate_writer"


def _route_after_candidate(state: ResearchAgentState) -> str:
    if state.get("status") == "failed":
        return END
    return "human_review"


def _route_after_review(state: ResearchAgentState) -> str:
    if state.get("status") == "approved":
        return "knowledge_promoter"
    return END


def build_graph(checkpointer):
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    builder = StateGraph(ResearchAgentState)
    builder.add_node("web_researcher", web_researcher)
    builder.add_node("knowledge_synthesizer", partial(knowledge_synthesizer, llm=llm))
    builder.add_node("candidate_writer", candidate_writer)
    builder.add_node("human_review", human_review)
    builder.add_node("knowledge_promoter", knowledge_promoter)

    builder.set_entry_point("web_researcher")
    builder.add_edge("web_researcher", "knowledge_synthesizer")
    builder.add_conditional_edges(
        "knowledge_synthesizer",
        _route_after_synthesis,
        {"candidate_writer": "candidate_writer", END: END},
    )
    builder.add_conditional_edges(
        "candidate_writer",
        _route_after_candidate,
        {"human_review": "human_review", END: END},
    )
    builder.add_conditional_edges(
        "human_review",
        _route_after_review,
        {"knowledge_promoter": "knowledge_promoter", END: END},
    )
    builder.add_edge("knowledge_promoter", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],  # S5-AA-007: pause for expert review
    )
