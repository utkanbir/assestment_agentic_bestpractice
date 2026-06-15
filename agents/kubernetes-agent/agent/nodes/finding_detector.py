import json

from langchain_core.messages import SystemMessage

from agent.state import KubernetesAgentState


_SYSTEM = """Kubernetes assessment uzmanısın. Interview cevabını analiz et.
Eğer önemli bir bulgu varsa JSON döndür:
{
  "has_finding": true,
  "description": "...",
  "severity": "critical|high|medium|low|info",
  "confidence": 0.0-1.0,
  "area": "cluster_architecture|networking|security|observability|capacity|disaster_recovery|cicd|workload_management"
}
Bulgu yoksa: {"has_finding": false}
Bulgu MUTLAKA somut bir teknik gözleme dayanmalı."""


async def finding_detector(state: KubernetesAgentState, llm) -> dict:
    answer = state.get("last_answer", "")
    question = state.get("current_question", "")
    evidence_list = state.get("pending_evidence", [])
    last_evidence = evidence_list[-1] if evidence_list else None

    if not last_evidence:
        return {}

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Soru: {question}\nCevap: {answer}\nKanıt: {json.dumps(last_evidence, ensure_ascii=False)}"),
    ]

    response = await llm.ainvoke(messages)

    try:
        result = json.loads(response.content.strip())
    except (json.JSONDecodeError, ValueError):
        return {}

    if not result.get("has_finding"):
        return {}

    pending = list(state.get("pending_findings", []))
    covered = list(state.get("covered_areas", []))

    pending.append({
        "description": result["description"],
        "severity": result["severity"],
        "confidence": result["confidence"],
        "area": result.get("area", ""),
        "evidence_index": len(state.get("pending_evidence", [])) - 1,
    })

    area = result.get("area", "")
    if area and area not in covered:
        covered.append(area)

    should_end = state.get("answer_count", 0) >= 8 or len(covered) >= 8

    return {
        "pending_findings": pending,
        "covered_areas": covered,
        "should_end_interview": should_end,
        "human_approval_required": result["severity"] in ("critical", "high"),
    }
