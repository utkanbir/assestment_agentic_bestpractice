import json

from langchain_core.messages import SystemMessage

from agent.state import WorkstreamAgentState

_SYSTEM = """Verilen interview cevabından kanıt çıkar.
JSON formatında yanıt ver: {"source": "...", "content": "...", "evidence_type": "interview"}
content: cevabın önemli teknik detaylarını içermeli (max 500 karakter)."""


async def evidence_capture(state: WorkstreamAgentState, llm) -> dict:
    answer = state.get("last_answer", "")
    question = state.get("current_question", "")

    if not answer.strip():
        return {"pending_evidence": state.get("pending_evidence", []), "evidence_captured": False}

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Soru: {question}\nCevap: {answer}"),
    ]
    response = await llm.ainvoke(messages)

    try:
        evidence_data = json.loads(response.content.strip())
    except (json.JSONDecodeError, ValueError):
        evidence_data = {"source": "interview", "content": answer[:500], "evidence_type": "interview"}

    if not evidence_data.get("content", "").strip():
        return {"pending_evidence": state.get("pending_evidence", []), "evidence_captured": False}

    evidence_data["interview_id"] = state.get("interview_id")
    pending = list(state.get("pending_evidence", []))
    pending.append(evidence_data)
    return {"pending_evidence": pending, "evidence_captured": True}
