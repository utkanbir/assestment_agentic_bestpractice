import json

from langchain_core.messages import SystemMessage

from agent.config import settings
from agent.state import WorkstreamAgentState

_SYSTEM_TMPL = """{workstream_label} assessment uzmanısın. Interview cevabını analiz et.
Eğer önemli bir bulgu varsa JSON döndür:
{{
  "has_finding": true,
  "description": "...",
  "severity": "critical|high|medium|low|info",
  "confidence": 0.0-1.0,
  "area": "kısa alan adı (workstream ile ilgili)"
}}
Bulgu yoksa: {{"has_finding": false}}
Bulgu MUTLAKA somut bir teknik gözleme dayanmalı."""


def _similar_context(similar_findings: list[dict]) -> str:
    if not similar_findings:
        return ""
    lines = ["\n\nGeçmiş benzer bulgular (Qdrant — kalibrasyon için kullan):"]
    for i, f in enumerate(similar_findings[:3], 1):
        score = f.get("score", 0)
        desc = f.get("description", "")[:120]
        sev = f.get("severity", "")
        conf = f.get("confidence", "")
        lines.append(f"  {i}. [score={score:.2f}] severity={sev} confidence={conf}: {desc}")
    return "\n".join(lines)


async def finding_detector(state: WorkstreamAgentState, llm) -> dict:
    workstream = state.get("workstream") or settings.workstream
    label = workstream.replace("_", " ").title()
    system_prompt = _SYSTEM_TMPL.format(workstream_label=label)

    answer = state.get("last_answer", "")
    question = state.get("current_question", "")
    evidence_list = state.get("pending_evidence", [])
    last_evidence = evidence_list[-1] if evidence_list else None

    if not last_evidence:
        return {}

    similar_ctx = _similar_context(state.get("similar_findings", []))
    messages = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=(
            f"Soru: {question}\nCevap: {answer}\n"
            f"Kanıt: {json.dumps(last_evidence, ensure_ascii=False)}"
            f"{similar_ctx}"
        )),
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
        "evidence_index": len(evidence_list) - 1,
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
