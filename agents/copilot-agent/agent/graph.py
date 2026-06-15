# S5-AA-004/005: Ontology Co-Pilot Agent graph
from functools import partial

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from agent.config import settings
from agent.state import CopilotState
from agent.nodes.proposal_parser import proposal_parser
from agent.nodes.shacl_validator import shacl_validator
from agent.nodes.human_review import human_review
from agent.nodes.knowledge_publisher import knowledge_publisher


def _route_after_validation(state: CopilotState) -> str:
    if state.get("status") == "failed":
        return END
    return "human_review"


def _route_after_review(state: CopilotState) -> str:
    if state.get("status") == "approved":
        return "knowledge_publisher"
    return END


def build_graph(checkpointer):
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    builder = StateGraph(CopilotState)
    builder.add_node("proposal_parser", partial(proposal_parser, llm=llm))
    builder.add_node("shacl_validator", shacl_validator)
    builder.add_node("human_review", human_review)
    builder.add_node("knowledge_publisher", knowledge_publisher)

    builder.set_entry_point("proposal_parser")
    builder.add_edge("proposal_parser", "shacl_validator")
    builder.add_conditional_edges(
        "shacl_validator",
        _route_after_validation,
        {"human_review": "human_review", END: END},
    )
    builder.add_conditional_edges(
        "human_review",
        _route_after_review,
        {"knowledge_publisher": "knowledge_publisher", END: END},
    )
    builder.add_edge("knowledge_publisher", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],  # S5-AA-005: pause for human decision
    )
