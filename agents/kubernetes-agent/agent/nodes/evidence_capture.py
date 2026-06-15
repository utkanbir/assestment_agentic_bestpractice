from langchain_core.messages import SystemMessage

from agent.state import KubernetesAgentState


_SYSTEM = """Verilen interview cevabından kanıt çıkar.
JSON formatında yanıt ver: {"source": "...", "content": "...", "evidence_type": "interview"}
content: cevabın önemli teknik detaylarını içermeli (max 500 karakter)."""


async def evidence_capture(state: KubernetesAgentState, llm) -> dict:
    answer = state.get("last_answer", "")
    question = state.get("current_question", "")

    if not answer.strip():
        return {"pending_evidence": state.get("pending_evidence", [])}

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Soru: {question}\nCevap: {answer}"),
    ]

    response = await llm.ainvoke(messages)

    import json
    try:
        evidence_data = json.loads(response.content.strip())
    except (json.JSONDecodeError, ValueError):
        evidence_data = {
            "source": "interview",
            "content": answer[:500],
            "evidence_type": "interview",
        }

    evidence_data["interview_id"] = state.get("interview_id")

    pending = list(state.get("pending_evidence", []))
    pending.append(evidence_data)

    return {"pending_evidence": pending}
