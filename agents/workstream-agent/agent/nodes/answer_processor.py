from langchain_core.messages import HumanMessage

from agent.state import WorkstreamAgentState


async def answer_processor(state: WorkstreamAgentState) -> dict:
    answer = state.get("last_answer", "")
    question = state.get("current_question", "")
    return {
        "messages": [HumanMessage(content=f"Q: {question}\nA: {answer}")],
        "answer_count": state.get("answer_count", 0) + 1,
    }
