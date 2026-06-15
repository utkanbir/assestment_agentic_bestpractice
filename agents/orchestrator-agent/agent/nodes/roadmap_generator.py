# S4-AA-007: Consolidated roadmap generator (8 roadmap → öncelikli 1 plan)
from pathlib import Path
import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from SPARQLWrapper import SPARQLWrapper, JSON
from agent.config import settings
from agent.state import OrchestratorState

_ROADMAP_SPARQL = Path(__file__).parents[3] / "knowledge" / "sparql" / "orchestrator" / "03_consolidated_roadmap.sparql"

_llm = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
    max_tokens=3000,
)

_ROADMAP_PROMPT = """Aşağıdaki 8 workstream'den gelen recommendation'ları tek konsolide roadmap'e dönüştür.

Öneriler (SPARQL'den, horizon ve priority sıralı):
{recommendations}

Cross-task bağımlılıklar göz önünde bulundurulacak:
{dependencies}

Kurallar:
1. Kısa vadeli (0-3 ay): critical risk'leri çözen aksiyonlar önce
2. Çakışan önerileri birleştir, tekrarları kaldır
3. Bağımlılık sırasına göre sırala (örn. Ingestion altyapısı CDP'den önce)
4. Her roadmap item için: başlık, açıklama, horizon, öncelik, etkilenen workstream'ler, tahmini efor
5. JSON array döndür: [{{"title":"...","description":"...","horizon":"short|medium|long","priority":1,"workstreams":[],"effort":"...","addresses_conflict":false}}]"""


def _run_roadmap_query() -> list[dict]:
    sparql = SPARQLWrapper(
        f"{settings.fuseki_url}/{settings.fuseki_dataset}/sparql",
        agent="AAKP-Orchestrator/1.0",
    )
    sparql.setCredentials(settings.fuseki_user, settings.fuseki_password)
    sparql.setQuery(_ROADMAP_SPARQL.read_text(encoding="utf-8"))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    rows = []
    for r in results["results"]["bindings"]:
        rows.append({k: v["value"] for k, v in r.items()})
    return rows


async def roadmap_generator(state: OrchestratorState) -> dict:
    try:
        kg_items = _run_roadmap_query()
    except Exception:
        kg_items = []

    rec_text = "\n".join(
        f"  [{r.get('horizonLabel', '?')}] P{r.get('priorityValue', '?')} "
        f"— {r.get('recTitle', r.get('recommendation', '')[:40])} "
        f"(ws: {r.get('workstream', '?')}, risk: {r.get('riskSeverity', '?')})"
        for r in kg_items[:30]
    ) or "  (roadmap verisi yok)"

    dep_text = "\n".join(
        f"  {r.get('workstreamA')} → {r.get('workstreamB')} ({r.get('sharedCapabilityArea', '')})"
        for r in state.cross_task_dependencies[:10]
    ) or "  (bağımlılık yok)"

    prompt = _ROADMAP_PROMPT.format(recommendations=rec_text, dependencies=dep_text)

    try:
        resp = await _llm.ainvoke([HumanMessage(content=prompt)])
        import json, re
        text = resp.content
        m = re.search(r"\[.*\]", text, re.DOTALL)
        roadmap = json.loads(m.group()) if m else []
    except Exception:
        roadmap = []

    # Persist each roadmap item to API
    try:
        async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=60) as client:
            for item in roadmap:
                await client.post("/api/v1/recommendations", json={
                    "assessment_id": state.assessment_id,
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "horizon": item.get("horizon", "medium"),
                    "priority": item.get("priority", 3),
                    "workstreams": item.get("workstreams", []),
                    "effort": item.get("effort", ""),
                    "consolidated": True,
                })
    except Exception:
        pass

    return {"consolidated_roadmap": roadmap}
