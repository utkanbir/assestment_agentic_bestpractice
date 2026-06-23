"""Fuseki + PostgreSQL aggregates for platform Knowledge Graph dashboard."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_learning import AgentLearningEvent
from app.models.assessment import Answer, Question
from app.services.protege_export import load_ontology_graph
from app.services.sparql_client import sparql_client
from rdflib import OWL, RDF

_ASSESSMENT_GRAPH = "<https://aakp.ai/graph/assessment>"
_AGENTS_GRAPH = "<https://aakp.ai/graph/agents>"


def _count(binding: dict, key: str = "c") -> int:
    try:
        return int(binding.get(key, {}).get("value", 0))
    except (TypeError, ValueError):
        return 0


async def _sparql_count(sparql: str, key: str = "c") -> int | None:
    try:
        result = await sparql_client.query(sparql)
        rows = result.get("results", {}).get("bindings", [])
        if not rows:
            return 0
        return _count(rows[0], key)
    except Exception:
        return None


async def _count_type(class_uri: str, graph: str = _ASSESSMENT_GRAPH) -> int | None:
    return await _sparql_count(f"""
SELECT (COUNT(DISTINCT ?x) AS ?c) WHERE {{
  GRAPH {graph} {{ ?x a {class_uri} }}
}}
""")


async def fetch_kg_stats(db: AsyncSession) -> dict:
    fuseki_ok = True
    checks: list[int | None] = []

    def track(v: int | None) -> int:
        nonlocal fuseki_ok
        checks.append(v)
        if v is None:
            fuseki_ok = False
        return v or 0

    assessments = track(await _count_type("aakp:Assessment"))
    tasks = track(await _count_type("aakp:Task"))
    interviews = track(await _count_type("aakp:Interview"))
    questions = track(await _count_type("aakp:Question"))
    answers = track(await _count_type("aakp:Answer"))
    evaluations = track(await _count_type("aakp:Evaluation"))
    findings = track(await _count_type("aakp:Finding"))
    consultants = track(await _count_type("aakp:Consultant"))
    evidence = track(await _count_type("aakp:Evidence"))
    assessment_agents = track(await _count_type("aakp:AssessmentAgent", _AGENTS_GRAPH))
    training = track(await _count_type("aakp:TrainingInteraction"))
    knowledge = track(await _count_type("aakp:AgentKnowledge"))
    concept_links = track(await _sparql_count(f"""
SELECT (COUNT(*) AS ?c) WHERE {{
  GRAPH {_ASSESSMENT_GRAPH} {{ ?e aakp:refersToConcept ?c }}
}}
"""))

    triples_agents = track(await _sparql_count(f"""
SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH {_AGENTS_GRAPH} {{ ?s ?p ?o }} }}
"""))
    triples_assessment = track(await _sparql_count(f"""
SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH {_ASSESSMENT_GRAPH} {{ ?s ?p ?o }} }}
"""))
    triples_total = triples_agents + triples_assessment

    individuals = track(await _sparql_count(f"""
SELECT (COUNT(DISTINCT ?ind) AS ?c) WHERE {{
  {{
    GRAPH {_AGENTS_GRAPH} {{ ?ind a ?type }}
  }} UNION {{
    GRAPH {_ASSESSMENT_GRAPH} {{ ?ind a ?type }}
  }}
  FILTER(isIRI(?ind))
}}
"""))

    by_workstream: list[dict] = []
    try:
        ws_rows = await sparql_client.query(f"""
SELECT ?ws
  (COUNT(DISTINCT ?ans) AS ?answers)
  (COUNT(DISTINCT ?q) AS ?questions)
  (COUNT(DISTINCT ?tr) AS ?training)
  (COUNT(DISTINCT ?kn) AS ?knowledge)
WHERE {{
  GRAPH {_ASSESSMENT_GRAPH} {{
    OPTIONAL {{
      ?t a aakp:Task ; aakp:hasWorkstream ?ws .
      ?i a aakp:Interview ; aakp:conductedForTask ?t .
      ?q a aakp:Question ; aakp:askedInInterview ?i .
      OPTIONAL {{ ?ans a aakp:Answer ; aakp:answersQuestion ?q }}
    }}
    OPTIONAL {{ ?tr a aakp:TrainingInteraction ; aakp:forWorkstream ?ws }}
    OPTIONAL {{ ?kn a aakp:AgentKnowledge ; aakp:forWorkstream ?ws }}
    FILTER(BOUND(?ws))
  }}
}}
GROUP BY ?ws
ORDER BY ?ws
""")
        for row in ws_rows.get("results", {}).get("bindings", []):
            ws = row.get("ws", {}).get("value", "")
            if not ws:
                continue
            ac = _count(row, "answers")
            qc = _count(row, "questions")
            tc = _count(row, "training")
            kc = _count(row, "knowledge")
            by_workstream.append({
                "workstream": ws,
                "answer_count": ac,
                "question_count": qc,
                "training_count": tc,
                "knowledge_count": kc,
                "total_pieces": ac + tc + kc,
            })
    except Exception:
        fuseki_ok = False

    pg_learning = await db.scalar(select(func.count()).select_from(AgentLearningEvent)) or 0
    pg_aaha = await db.scalar(
        select(func.count()).select_from(AgentLearningEvent).where(AgentLearningEvent.mode == "aaha")
    ) or 0
    pg_docs = await db.scalar(
        select(func.count()).select_from(AgentLearningEvent).where(AgentLearningEvent.mode == "document")
    ) or 0
    pg_text = await db.scalar(
        select(func.count()).select_from(AgentLearningEvent).where(AgentLearningEvent.mode == "text")
    ) or 0
    pg_answers = await db.scalar(select(func.count()).select_from(Answer)) or 0
    pg_questions = await db.scalar(select(func.count()).select_from(Question)) or 0
    pg_evaluations = await db.scalar(
        select(func.count()).select_from(Answer).where(Answer.evaluation.isnot(None), Answer.evaluation != "")
    ) or 0

    try:
        onto = load_ontology_graph(include_instances=False)
        ontology_classes = len(list(onto.subjects(RDF.type, OWL.Class)))
    except Exception:
        ontology_classes = 0

    return {
        "source": "fuseki" if fuseki_ok else "partial",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "individuals": individuals,
            "triples_total": triples_total,
            "triples_assessment_graph": triples_assessment,
            "triples_agents_graph": triples_agents,
            "assessments": assessments,
            "tasks": tasks,
            "interviews": interviews,
            "questions": questions,
            "answers": answers,
            "evaluations": evaluations,
            "findings": findings,
            "consultants": consultants,
            "evidence": evidence,
            "assessment_agents": assessment_agents,
            "training_interactions": training,
            "agent_knowledge": knowledge,
            "concept_links": concept_links,
            "learning_pieces": training + knowledge,
            "ontology_classes": ontology_classes,
        },
        "postgres": {
            "learning_events": pg_learning,
            "aaha_count": pg_aaha,
            "text_count": pg_text,
            "document_count": pg_docs,
            "answers": pg_answers,
            "questions": pg_questions,
            "evaluations": pg_evaluations,
        },
        "by_workstream": by_workstream,
    }
