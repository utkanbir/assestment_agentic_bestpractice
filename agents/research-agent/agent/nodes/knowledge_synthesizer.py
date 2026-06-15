# S5-AA-006: Synthesize web results into candidate ontology triples
import json
import logging

from langchain_core.messages import SystemMessage

from agent.state import ResearchAgentState

log = logging.getLogger(__name__)

_SYSTEM = """Sen AAKP ontoloji mühendisisin. Web araştırma sonuçlarını analiz et ve
ilgili bilgiyi RDF üçlüleri olarak candidate knowledge graph'a eklemek için hazırla.

SADECE aşağıdaki JSON formatında döndür:
{
  "summary": "araştırma özeti (Türkçe, 3-5 cümle)",
  "triples": [
    {"subject": "aakp:Concept", "predicate": "rdfs:label", "object": "\"label\"@tr"},
    ...
  ],
  "sparql_insert": "INSERT DATA { GRAPH <urn:aakp:candidate> { ... } }"
}

Prefix'ler: aakp:, mat:, rdfs:, owl:, xsd:
Domain bağlamı: Migros veri platformu değerlendirmesi, Türkiye perakende sektörü."""


async def knowledge_synthesizer(state: ResearchAgentState, llm) -> dict:
    web_results = state.get("web_results", [])
    context = "\n\n".join(
        f"[{i+1}] {r['title']}\n{r['snippet']}" for i, r in enumerate(web_results)
    ) or "Web sonucu bulunamadı."

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Konu: {state['topic']}\nDomain: {state['domain']}\n\nWeb Sonuçları:\n{context}"),
    ]
    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return {
            "synthesized_summary": data.get("summary", ""),
            "candidate_triples": data.get("triples", []),
            "sparql_insert": data.get("sparql_insert", ""),
            "human_review_required": True,  # S5-AA-007: always review before publish
            "status": "pending",
        }
    except Exception as exc:
        log.error("Knowledge synthesis failed: %s", exc)
        return {"status": "failed"}
