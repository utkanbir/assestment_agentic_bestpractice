import json
import logging

import httpx
from langchain_core.messages import SystemMessage

from agent.config import settings
from agent.state import WorkstreamAgentState

logger = logging.getLogger(__name__)

_SYSTEM_TMPL = """Sen bir {workstream_label} risk analisti uzmansın.
Verilen teknik bulgudan (Finding) somut bir risk türet.
SADECE aşağıdaki JSON formatını döndür, başka açıklama ekleme:
{{
  "title": "kısa risk başlığı (maks 80 karakter)",
  "description": "Bu bulgununun risk perspektifinden açıklaması",
  "severity": "critical|high|medium|low",
  "impact": "Etkisi gerçekleşirse ne olur? Sistemler, SLA, veri, güvenlik açısından."
}}

Kurallar:
- severity: bulgunun severity'siyle aynı veya bir altı olabilir
- title: Türkçe, eylem bildiren kısa cümle
- impact: somut, ölçülebilir"""


async def risk_reasoner(state: WorkstreamAgentState, llm) -> dict:
    approved_ids = state.get("approved_finding_ids", [])
    if not approved_ids:
        return {"generated_risks": []}

    workstream = state.get("workstream") or settings.workstream
    label = workstream.replace("_", " ").title()
    system_prompt = _SYSTEM_TMPL.format(workstream_label=label)
    generated = []

    async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=30) as client:
        for finding_id in approved_ids:
            resp = await client.get(f"/api/v1/findings/{finding_id}")
            if resp.status_code != 200:
                continue
            finding = resp.json()

            messages = [
                SystemMessage(content=system_prompt),
                SystemMessage(content=(
                    f"Finding:\n"
                    f"  description: {finding['description']}\n"
                    f"  severity: {finding['severity']}\n"
                    f"  confidence: {finding['confidence']}"
                )),
            ]

            try:
                response = await llm.ainvoke(messages)
                raw = response.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                risk_data = json.loads(raw)
            except (json.JSONDecodeError, ValueError, IndexError) as exc:
                logger.warning("LLM risk parse failed for finding %s: %s", finding_id, exc)
                continue

            risk_resp = await client.post("/api/v1/risks", json={
                "finding_id": finding_id,
                "title": risk_data.get("title", "")[:500],
                "description": risk_data.get("description", ""),
                "level": risk_data.get("severity", finding["severity"]),
                "impact": risk_data.get("impact", ""),
            })

            if risk_resp.status_code == 201:
                risk = risk_resp.json()
                generated.append({
                    "risk_id": risk["id"],
                    "finding_id": finding_id,
                    "title": risk["title"],
                    "level": risk["level"],
                    "impact": risk["impact"],
                })

    return {"generated_risks": generated}
