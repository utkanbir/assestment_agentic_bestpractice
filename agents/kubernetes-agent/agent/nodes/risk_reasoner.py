"""
S2-AA-001: Finding → Risk reasoning node.

For each approved finding written to PG/KG, asks the LLM to derive
a concrete Risk (what can go wrong, impact, severity). Writes the risk
back via the API (which triggers kg_writer → Fuseki in background).
"""
import json
import logging

import httpx
from langchain_core.messages import SystemMessage

from agent.config import settings
from agent.state import KubernetesAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """Sen bir Kubernetes risk analisti uzmansın.
Verilen teknik bulgudan (Finding) somut bir risk türet.
SADECE aşağıdaki JSON formatını döndür, başka açıklama ekleme:
{
  "title": "kısa risk başlığı (maks 80 karakter)",
  "description": "Bu bulgununun risk perspektifinden açıklaması",
  "severity": "critical|high|medium|low",
  "impact": "Etkisi gerçekleşirse ne olur? Sistemler, SLA, veri, güvenlik açısından."
}

Kurallar:
- severity: bulgunun severity'siyle aynı veya bir altı olabilir
- title: Türkçe, eylem bildiren kısa cümle ("RBAC denetim eksikliği veri sızıntısına yol açar")
- impact: somut, ölçülebilir; "etkilenebilir" gibi belirsiz ifadelerden kaçın"""


async def risk_reasoner(state: KubernetesAgentState, llm) -> dict:
    approved_ids = state.get("approved_finding_ids", [])
    if not approved_ids:
        return {"generated_risks": []}

    generated = []

    async with httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=30
    ) as client:
        for finding_id in approved_ids:
            # Fetch finding details from API
            resp = await client.get(f"/api/v1/findings/{finding_id}")
            if resp.status_code != 200:
                logger.warning("Could not fetch finding %s: %s", finding_id, resp.status_code)
                continue
            finding = resp.json()

            # LLM: derive risk from finding
            messages = [
                SystemMessage(content=_SYSTEM),
                SystemMessage(
                    content=(
                        f"Finding:\n"
                        f"  description: {finding['description']}\n"
                        f"  severity: {finding['severity']}\n"
                        f"  confidence: {finding['confidence']}"
                    )
                ),
            ]

            try:
                response = await llm.ainvoke(messages)
                raw = response.content.strip()
                # Strip possible markdown fences
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                risk_data = json.loads(raw)
            except (json.JSONDecodeError, ValueError, IndexError) as exc:
                logger.warning("LLM risk parse failed for finding %s: %s", finding_id, exc)
                continue

            # Write Risk to API (triggers PG + background KG write)
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
            else:
                logger.warning("Risk creation failed for finding %s: %s %s",
                               finding_id, risk_resp.status_code, risk_resp.text)

    return {"generated_risks": generated}
