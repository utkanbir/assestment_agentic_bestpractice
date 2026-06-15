import json

import httpx
import websockets
from langchain_core.messages import AIMessage, SystemMessage

from agent.config import settings
from agent.state import WorkstreamAgentState

_SYSTEM_TMPL = """Sen bir {workstream_label} değerlendirme uzmanısın.
Mevcut bulgular ve kapsanan alanlar ışığında en kritik sonraki soruyu Türkçe sor.
Yanıtın SADECE soru cümlesi olsun, başka hiçbir şey olmasın."""


async def question_advisor(state: WorkstreamAgentState, llm) -> dict:
    workstream = state.get("workstream") or settings.workstream
    label = workstream.replace("_", " ").title()

    covered = set(state.get("covered_areas", []))
    findings_summary = json.dumps(state.get("existing_findings", [])[:5], ensure_ascii=False)

    # Fetch question bank from API
    bank_hint = "Workstream kapsamındaki kritik alanları sorgula."
    async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=10) as client:
        bank_resp = await client.get(f"/api/v1/question-bank?workstream={workstream}")
        if bank_resp.status_code == 200:
            bank = bank_resp.json()
            uncovered = [q for q in bank if q.get("area") not in covered]
            if uncovered:
                bank_hint = uncovered[0]["text"]

    messages = [
        SystemMessage(content=_SYSTEM_TMPL.format(workstream_label=label)),
        *state.get("messages", [])[-6:],
        SystemMessage(content=f"Soru bankası önerisi: {bank_hint}\nMevcut bulgular: {findings_summary}"),
    ]

    response = await llm.ainvoke(messages)
    question = response.content.strip()

    interview_id = state.get("interview_id")
    if interview_id:
        try:
            ws_url = f"{settings.ws_base_url.replace('http', 'ws')}/ws/interviews/{interview_id}"
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps({
                    "event": "question.suggested",
                    "payload": {"question": question, "source": "agent", "workstream": workstream},
                }))
        except Exception:
            pass

    return {
        "current_question": question,
        "messages": [AIMessage(content=question)],
    }
