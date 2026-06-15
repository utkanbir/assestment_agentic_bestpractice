# S4-AA-004: Conflict detector — çelişen findings → human review queue
import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from agent.config import settings
from agent.state import OrchestratorState

_llm = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
    max_tokens=1024,
)

_CONFLICT_PROMPT = """Aşağıdaki cross-task risk çakışmalarını incele ve gerçek çelişkiler ile tesadüfi örtüşmeleri ayırt et.

Çakışmalar (workstream A vs B, aynı capability area, farklı severity):
{conflicts}

Her çakışma için:
1. GERÇEKTİR: Aynı sistem için farklı risk değerlendirmesi → human review gerekli
2. NORMALDIR: Farklı perspektiften aynı capability → çakışma değil

JSON array döndür: [{{"conflict_key": "...", "type": "REAL|NORMAL", "reason": "...", "recommended_action": "..."}}]"""


async def conflict_detector(state: OrchestratorState) -> dict:
    if not state.shared_risk_areas:
        return {"conflicts": [], "conflicts_pending_review": [], "human_review_required": False}

    conflict_text = "\n".join(
        f"- {r.get('workstreamA')} vs {r.get('workstreamB')}: {r.get('sharedCapabilityArea')} "
        f"(severity: {r.get('riskSeverityA')} vs {r.get('riskSeverityB')})"
        for r in state.shared_risk_areas[:20]
    )

    try:
        resp = await _llm.ainvoke([HumanMessage(content=_CONFLICT_PROMPT.format(conflicts=conflict_text))])
        import json, re
        text = resp.content
        m = re.search(r"\[.*\]", text, re.DOTALL)
        analysis = json.loads(m.group()) if m else []
    except Exception:
        analysis = []

    real_conflicts = [a for a in analysis if a.get("type") == "REAL"]
    conflict_ids = [a["conflict_key"] for a in real_conflicts]

    return {
        "conflicts": real_conflicts,
        "conflicts_pending_review": conflict_ids,
        "human_review_required": len(real_conflicts) > 0,
        "messages": [{"role": "assistant", "content": f"{len(real_conflicts)} çelişki tespit edildi, human review gerekiyor."}]
        if real_conflicts else [],
    }
