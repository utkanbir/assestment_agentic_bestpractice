from langchain_core.messages import HumanMessage

from agent.state import KubernetesAgentState


async def answer_processor(state: KubernetesAgentState) -> dict:
    answer = state.get("last_answer", "")
    question = state.get("current_question", "")

    new_message = HumanMessage(content=f"Q: {question}\nA: {answer}")

    return {
        "messages": [new_message],
        "answer_count": state.get("answer_count", 0) + 1,
    }
