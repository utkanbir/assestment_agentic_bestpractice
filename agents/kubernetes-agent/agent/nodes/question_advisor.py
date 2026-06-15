import json

import websockets
from langchain_core.messages import AIMessage, SystemMessage

from agent.config import settings
from agent.question_bank import QUESTION_BANK
from agent.state import KubernetesAgentState


_SYSTEM = """Sen bir Kubernetes altyapı değerlendirme uzmanısın.
Mevcut bulgular ve kapsanan alanlar ışığında en kritik sonraki soruyu Türkçe sor.
Yanıtın SADECE soru cümlesi olsun, başka hiçbir şey olmasın."""


async def question_advisor(state: KubernetesAgentState, llm) -> dict:
    covered = set(state.get("covered_areas", []))
    findings_summary = json.dumps(state.get("existing_findings", [])[:5], ensure_ascii=False)

    uncovered = [q for q in QUESTION_BANK if q["area"] not in covered]
    bank_hint = uncovered[0]["text"] if uncovered else "Tüm alanlar kapsandı."

    messages = [
        SystemMessage(content=_SYSTEM),
        *state.get("messages", [])[-6:],
        SystemMessage(content=f"Soru bankası önerisi: {bank_hint}\nMevcut bulgular: {findings_summary}"),
    ]

    response = await llm.ainvoke(messages)
    question = response.content.strip()

    # Fast path: WebSocket ile frontend'e gönder
    interview_id = state.get("interview_id")
    if interview_id:
        try:
            ws_url = f"{settings.ws_base_url.replace('http', 'ws')}/ws/interviews/{interview_id}"
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps({
                    "event": "question.suggested",
                    "payload": {"question": question, "source": "agent"},
                }))
        except Exception:
            pass  # WebSocket hata olsa da devam et

    return {
        "current_question": question,
        "messages": [AIMessage(content=question)],
    }
