# S4-AA-006: Executive summary generator (C-level, TR/EN)
import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from agent.config import settings
from agent.state import OrchestratorState

_llm = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
    max_tokens=2048,
)

_EXEC_PROMPT = """Sen kıdemli bir veri platformu danışmanısın. Aşağıdaki assessment verilerine dayanarak C-level yöneticiler için kısa ve etkili bir executive summary yaz.

Assessment ID: {assessment_id}
Tamamlanan workstream'ler: {completed_count}/{total_count}
Toplam risk sayısı: {total_risks}

Risk dağılımı (en kritik alanlar):
{top_risks}

Cross-task bağımlılıklar: {dependency_count} bağımlılık, {conflict_count} çelişki

Çelişkiler (human review gerekiyor):
{conflicts}

Executive summary kuralları:
- Maksimum 300 kelime
- Critical ve high riskler öne çık
- Cross-task çelişkiler ayrıca vurgula
- Somut aksiyon önerileri ile bitir
- Hem Türkçe hem İngilizce paragraf yaz"""


async def executive_summary_gen(state: OrchestratorState) -> dict:
    top_risks = "\n".join(
        f"  - {r['capability_area']}: {r['severity'].upper()} ({r['risk_count']} risk, "
        f"workstream'ler: {', '.join(r['workstreams'][:3])})"
        for r in state.consolidated_risks[:5]
    ) or "  (risk verisi yok)"

    conflict_text = "\n".join(
        f"  - {c.get('conflict_key', '')}: {c.get('reason', '')}"
        for c in state.conflicts[:3]
    ) or "  (çelişki yok)"

    prompt = _EXEC_PROMPT.format(
        assessment_id=state.assessment_id,
        completed_count=len(state.completed_tasks),
        total_count=len(state.all_tasks),
        total_risks=sum(r["risk_count"] for r in state.consolidated_risks),
        top_risks=top_risks,
        dependency_count=len(state.cross_task_dependencies),
        conflict_count=len(state.conflicts),
        conflicts=conflict_text,
    )

    try:
        resp = await _llm.ainvoke([HumanMessage(content=prompt)])
        summary = resp.content
    except Exception as e:
        summary = f"Executive summary üretilemedi: {e}"

    # Persist to API
    try:
        async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=30) as client:
            await client.post("/api/v1/reports", json={
                "assessment_id": state.assessment_id,
                "report_type": "executive_summary",
                "title": f"Executive Summary — Assessment {state.assessment_id[:8]}",
                "content": summary,
            })
    except Exception:
        pass

    return {"executive_summary": summary}
