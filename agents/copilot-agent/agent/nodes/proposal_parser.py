# S5-AA-004: Parse natural language ontology proposal into candidate triples
import json
import logging

from langchain_core.messages import SystemMessage

from agent.state import CopilotState

log = logging.getLogger(__name__)

_SYSTEM = """Sen bir ontoloji mühendisisin. Kullanıcının doğal dil açıklamasını RDF üçlülerine dönüştür.
YALNIZCA aşağıdaki JSON formatında döndür, açıklama ekleme:
{
  "triples": [
    {"subject": "aakp:SubjectClass", "predicate": "rdfs:label", "object": "\"Açıklama\"@tr"},
    ...
  ],
  "sparql_insert": "INSERT DATA { GRAPH <urn:aakp:candidate> { ... } }"
}
Kullandığın prefix'ler: aakp:, mat:, rdfs:, owl:, xsd:"""


async def proposal_parser(state: CopilotState, llm) -> dict:
    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Öneri:\n{state['proposal_text']}"),
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
            "candidate_triples": data.get("triples", []),
            "sparql_insert": data.get("sparql_insert", ""),
            "status": "pending",
        }
    except Exception as exc:
        log.error("Proposal parse failed: %s", exc)
        return {"status": "failed", "validation_errors": [str(exc)]}
