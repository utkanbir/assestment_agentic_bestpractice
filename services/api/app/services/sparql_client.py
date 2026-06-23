import uuid
from pathlib import Path

import httpx

from app.core.config import settings

_PREFIXES = """
PREFIX aakp: <https://aakp.ai/ontology/assessment#>
PREFIX mat:  <https://aakp.ai/ontology/maturity#>
PREFIX arch: <https://aakp.ai/ontology/architecture#>
PREFIX org:  <https://aakp.ai/ontology/organization#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX sh:   <http://www.w3.org/ns/shacl#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
"""

_DATA_NS = "https://aakp.ai/data"

_INFERENCE_DIR = Path(__file__).parent.parent / "sparql" / "inference"
_SHACL_DIR = Path(__file__).parent.parent / "shacl"


def _uri(kind: str, uid: uuid.UUID) -> str:
    return f"{_DATA_NS}/{kind}/{uid}"


def _task_uri(task_id: uuid.UUID) -> str:
    return _uri("task", task_id)


def _finding_uri(finding_id: uuid.UUID) -> str:
    return _uri("finding", finding_id)


def _evidence_uri(evidence_id: uuid.UUID) -> str:
    return _uri("evidence", evidence_id)


def _interview_uri(interview_id: uuid.UUID) -> str:
    return _uri("interview", interview_id)


def _risk_uri(risk_id: uuid.UUID) -> str:
    return _uri("risk", risk_id)


def _assessment_uri(assessment_id: uuid.UUID) -> str:
    return _uri("assessment", assessment_id)


def _question_uri(question_id: uuid.UUID) -> str:
    return _uri("question", question_id)


def _answer_uri(answer_id: uuid.UUID) -> str:
    return _uri("answer", answer_id)


def _evaluation_uri(evaluation_id: uuid.UUID) -> str:
    return _uri("evaluation", evaluation_id)


def _consultant_uri(consultant_id: uuid.UUID) -> str:
    return _uri("consultant", consultant_id)


def _training_uri(event_id: uuid.UUID) -> str:
    return _uri("training", event_id)


def _agent_knowledge_uri(event_id: uuid.UUID) -> str:
    return _uri("agent-knowledge", event_id)


def _workstream_agent_uri(workstream: str) -> str:
    return f"{_DATA_NS}/agent/{workstream}"


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


_WORKSTREAM_LABELS: dict[str, str] = {
    "kubernetes": "Kubernetes Agent",
    "cloud_strategy": "Cloud Strategy Agent",
    "ingestion": "Data Ingestion Agent",
    "teradata_dr": "Teradata DR Agent",
    "lakehouse": "Lakehouse Agent",
    "governance": "Data Governance Agent",
    "data_product": "Data Product Agent",
    "cdp": "CDP Agent",
}


def _workstream_agent_label(workstream: str) -> str:
    return _WORKSTREAM_LABELS.get(workstream, workstream.replace("_", " ").title() + " Agent")


def _training_label(mode: str, question: str, max_len: int = 100) -> str:
    q = " ".join(question.split())
    if len(q) > max_len:
        q = q[: max_len - 1] + "…"
    return f"[{mode}] {q}"


def _knowledge_label(mode: str, content: str, filename: str | None = None, max_len: int = 100) -> str:
    if filename:
        return f"[{mode}] {filename}"
    c = " ".join(content.split())
    if len(c) > max_len:
        c = c[: max_len - 1] + "…"
    return f"[{mode}] {c}"


class SPARQLClient:
    def __init__(self):
        self._query_url = f"{settings.fuseki_url}/{settings.fuseki_dataset}/sparql"
        self._update_url = f"{settings.fuseki_url}/{settings.fuseki_dataset}/update"
        self._auth = ("admin", "aakp-fuseki-secret")

    async def query(self, sparql: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._query_url,
                params={"query": _PREFIXES + sparql},
                headers={"Accept": "application/sparql-results+json"},
                auth=self._auth,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def construct(self, sparql: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._query_url,
                params={"query": _PREFIXES + sparql},
                headers={"Accept": "text/turtle"},
                auth=self._auth,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.text

    async def update(self, sparql: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._update_url,
                data={"update": _PREFIXES + sparql},
                auth=self._auth,
                timeout=30,
            )
            resp.raise_for_status()

    # ── Assessment / Task / Interview ─────────────────────────────────────────

    async def insert_assessment(self, assessment_id: uuid.UUID,
                                 client_name: str, project_name: str,
                                 is_simulated: bool = False) -> str:
        uri = _assessment_uri(assessment_id)
        mode = "simulated" if is_simulated else "live"
        sim_val = "true" if is_simulated else "false"
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Assessment ;
             aakp:hasClientName  "{_escape(client_name)}" ;
             aakp:hasProjectName "{_escape(project_name)}" ;
             aakp:assessmentMode "{mode}" ;
             aakp:isSimulated    "{sim_val}"^^xsd:boolean ;
             aakp:pgId           "{assessment_id}" .
  }}
}}
""")
        return uri

    async def insert_task(self, task_id: uuid.UUID, assessment_id: uuid.UUID,
                           agent_type: str, workstream: str,
                           scope: str | None = None) -> str:
        uri = _uri("task", task_id)
        scope_triple = (
            f'<{uri}> aakp:hasScope "{_escape(scope)}" .'
            if scope else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Task ;
             aakp:belongsToAssessment <{_assessment_uri(assessment_id)}> ;
             aakp:hasAgentType        "{_escape(agent_type)}" ;
             aakp:hasWorkstream       "{_escape(workstream)}" ;
             aakp:pgId                "{task_id}" .
    {scope_triple}
  }}
}}
""")
        return uri

    async def insert_interview(self, interview_id: uuid.UUID, task_id: uuid.UUID,
                                interviewee_name: str,
                                interviewee_role: str | None = None) -> str:
        uri = _interview_uri(interview_id)
        role_triple = (
            f'<{uri}> aakp:intervieweeRole "{_escape(interviewee_role)}" .'
            if interviewee_role else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Interview ;
             aakp:conductedForTask  <{_task_uri(task_id)}> ;
             aakp:intervieweeName   "{_escape(interviewee_name)}" ;
             aakp:pgId              "{interview_id}" .
    {role_triple}
  }}
}}
""")
        return uri

    async def insert_question(self, question_id: uuid.UUID, interview_id: uuid.UUID, text: str, order: int = 0) -> str:
        uri = _question_uri(question_id)
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Question ;
             aakp:askedInInterview <{_interview_uri(interview_id)}> ;
             aakp:text "{_escape(text)}" ;
             aakp:questionOrder "{order}"^^xsd:integer ;
             aakp:pgId "{question_id}" .
    <{_interview_uri(interview_id)}> aakp:hasQuestion <{uri}> .
  }}
}}
""")
        return uri

    async def insert_answer(
        self,
        answer_id: uuid.UUID,
        question_id: uuid.UUID,
        text: str,
        consultant_comment: str | None = None,
    ) -> str:
        uri = _answer_uri(answer_id)
        comment_triple = (
            f'<{uri}> aakp:consultantComment "{_escape(consultant_comment)}" .'
            if consultant_comment else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Answer ;
             aakp:answersQuestion <{_question_uri(question_id)}> ;
             aakp:text "{_escape(text)}" ;
             aakp:pgId "{answer_id}" .
    <{_question_uri(question_id)}> aakp:hasAnswer <{uri}> .
    {comment_triple}
  }}
}}
""")
        return uri

    async def insert_consultant(
        self,
        consultant_id: uuid.UUID,
        assessment_id: uuid.UUID,
        first_name: str,
        last_name: str,
        role: str | None = None,
        expertise: str | None = None,
    ) -> str:
        uri = _consultant_uri(consultant_id)
        role_triple = f'<{uri}> aakp:consultantRole "{_escape(role)}" .' if role else ""
        expertise_triple = f'<{uri}> aakp:consultantExpertise "{_escape(expertise)}" .' if expertise else ""
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Consultant ;
             aakp:firstName "{_escape(first_name)}" ;
             aakp:lastName "{_escape(last_name)}" ;
             aakp:pgId "{consultant_id}" .
    {role_triple}
    {expertise_triple}
    <{_assessment_uri(assessment_id)}> aakp:hasConsultant <{uri}> .
  }}
}}
""")
        return uri

    async def link_consultant_to_answer(
        self,
        answer_id: uuid.UUID,
        consultant_id: uuid.UUID,
        consultant_comment: str | None = None,
    ) -> None:
        comment_triple = (
            f'<{_answer_uri(answer_id)}> aakp:consultantComment "{_escape(consultant_comment)}" .'
            if consultant_comment else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{_answer_uri(answer_id)}> aakp:reviewedByConsultant <{_consultant_uri(consultant_id)}> .
    {comment_triple}
  }}
}}
""")

    async def upsert_answer_evaluation(self, answer_id: uuid.UUID, text: str) -> str:
        """Replace prior Evaluation triples for this answer (supports re-evaluate)."""
        eval_id = uuid.uuid4()
        answer_uri = _answer_uri(answer_id)
        eval_uri = _evaluation_uri(eval_id)
        await self.update(f"""
DELETE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?ev ?p ?o .
    <{answer_uri}> aakp:hasEvaluation ?ev .
  }}
}}
INSERT {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{eval_uri}> a aakp:Evaluation ;
                 rdfs:label "AI Evaluation" ;
                 aakp:evaluationText "{_escape(text)}" ;
                 aakp:pgId "{eval_id}" .
    <{answer_uri}> aakp:hasEvaluation <{eval_uri}> .
  }}
}}
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    OPTIONAL {{
      ?ev a aakp:Evaluation .
      <{answer_uri}> aakp:hasEvaluation ?ev .
      ?ev ?p ?o .
    }}
  }}
}}
""")
        return eval_uri

    async def insert_evaluation(self, evaluation_id: uuid.UUID,
                                 answer_id: uuid.UUID, text: str) -> str:
        uri = _evaluation_uri(evaluation_id)
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Evaluation ;
             aakp:evaluationText "{_escape(text)}" ;
             aakp:pgId "{evaluation_id}" .
    <{_answer_uri(answer_id)}> aakp:hasEvaluation <{uri}> .
  }}
}}
""")
        return uri

    # ── Evidence ──────────────────────────────────────────────────────────────

    async def insert_evidence(self, evidence_id: uuid.UUID, interview_id: uuid.UUID | None,
                               source: str, content: str) -> str:
        uri = _evidence_uri(evidence_id)
        interview_triple = (
            f'<{uri}> aakp:collectedInInterview <{_interview_uri(interview_id)}> .'
            if interview_id else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:InterviewEvidence ;
             aakp:hasSource "{_escape(source)}" ;
             aakp:content   "{_escape(content)}" ;
             aakp:pgId      "{evidence_id}" .
    {interview_triple}
  }}
}}
""")
        return uri

    # ── Finding ───────────────────────────────────────────────────────────────

    async def insert_finding(self, finding_id: uuid.UUID, task_id: uuid.UUID,
                              evidence_id: uuid.UUID, description: str,
                              severity: str, confidence: float,
                              category: str | None = None) -> str:
        uri = _finding_uri(finding_id)
        # severity string → mat:Severity individual (e.g. mat:High)
        sev_individual = f"mat:{severity.capitalize()}"
        category_triple = (
            f'<{uri}> aakp:hasCategory "{_escape(category)}" .'
            if category else ""
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Finding ;
             aakp:identifiedInTask    <{_task_uri(task_id)}> ;
             aakp:supportedByEvidence <{_evidence_uri(evidence_id)}> ;
             aakp:description         "{_escape(description)}" ;
             mat:hasSeverity          {sev_individual} ;
             aakp:hasConfidence       "{confidence}"^^xsd:decimal ;
             aakp:approvalStatus      "pending" ;
             aakp:pgId                "{finding_id}" .
    {category_triple}
  }}
}}
""")
        return uri

    async def approve_finding(self, finding_id: uuid.UUID, status: str) -> None:
        uri = _finding_uri(finding_id)
        await self.update(f"""
DELETE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> aakp:approvalStatus ?old .
  }}
}}
INSERT {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> aakp:approvalStatus "{status}" .
  }}
}}
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> aakp:approvalStatus ?old .
  }}
}}
""")

    # ── Agent training (S24) ──────────────────────────────────────────────────

    async def insert_training_interaction(
        self,
        event_id: uuid.UUID,
        workstream: str,
        mode: str,
        question_text: str,
        answer_text: str,
        answer_author: str = "consultant",
    ) -> str:
        uri = _training_uri(event_id)
        agent_uri = _workstream_agent_uri(workstream)
        label = _training_label(mode, question_text)
        agent_label = _workstream_agent_label(workstream)
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{agent_uri}> a aakp:Task ;
                  aakp:hasWorkstream "{_escape(workstream)}" ;
                  rdfs:label "{_escape(agent_label)}" .
    <{uri}> a aakp:TrainingInteraction ;
             rdfs:label "{_escape(label)}" ;
             aakp:forWorkstream "{_escape(workstream)}" ;
             aakp:trainingMode "{_escape(mode)}" ;
             aakp:trainingQuestion "{_escape(question_text)}" ;
             aakp:trainingAnswer "{_escape(answer_text)}" ;
             aakp:answerAuthor "{_escape(answer_author)}" ;
             aakp:pgId "{event_id}" .
    <{agent_uri}> aakp:hasTrainingEvent <{uri}> .
  }}
}}
""")
        return uri

    async def insert_training_concept_links(
        self,
        event_id: uuid.UUID,
        concept_uris: list[str],
        *,
        knowledge_kind: str = "training",
    ) -> None:
        if not concept_uris:
            return
        ev_uri = (
            _training_uri(event_id)
            if knowledge_kind == "training"
            else _agent_knowledge_uri(event_id)
        )
        triples = "\n    ".join(
            f"<{ev_uri}> aakp:refersToConcept <{u}> ." for u in concept_uris
        )
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    {triples}
  }}
}}
""")

    async def insert_agent_knowledge(
        self,
        event_id: uuid.UUID,
        workstream: str,
        content: str,
        *,
        knowledge_mode: str = "text",
        source_doc_id: uuid.UUID | None = None,
        source_filename: str | None = None,
    ) -> str:
        uri = _agent_knowledge_uri(event_id)
        agent_uri = _workstream_agent_uri(workstream)
        label = _knowledge_label(knowledge_mode, content, source_filename)
        agent_label = _workstream_agent_label(workstream)
        extra = f'aakp:knowledgeMode "{_escape(knowledge_mode)}" ;\n             '
        if source_doc_id:
            extra += f'aakp:sourceDocId "{source_doc_id}" ;\n             '
        if source_filename:
            extra += f'aakp:sourceFilename "{_escape(source_filename)}" ;\n             '
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{agent_uri}> a aakp:Task ;
                  aakp:hasWorkstream "{_escape(workstream)}" ;
                  rdfs:label "{_escape(agent_label)}" .
    <{uri}> a aakp:AgentKnowledge ;
             rdfs:label "{_escape(label)}" ;
             aakp:forWorkstream "{_escape(workstream)}" ;
             {extra}aakp:knowledgeContent "{_escape(content[:2000])}" ;
             aakp:pgId "{event_id}" .
    <{agent_uri}> aakp:hasAgentKnowledge <{uri}> .
  }}
}}
""")
        return uri

    async def delete_learning_by_pg_id(self, event_id: uuid.UUID) -> None:
        """Remove training/knowledge triples and agent links for a learning event."""
        pg = str(event_id)
        await self.update(f"""
DELETE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?s ?p ?o .
    ?agent ?link ?s .
  }}
}}
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?s aakp:pgId "{pg}" .
    OPTIONAL {{ ?s ?p ?o }}
    OPTIONAL {{
      ?agent ?link ?s .
      FILTER(?link IN (aakp:hasTrainingEvent, aakp:hasAgentKnowledge))
    }}
  }}
}}
""")

    # ── Risk (S2-AA-001) ─────────────────────────────────────────────────────

    async def insert_risk(self, risk_id: uuid.UUID, finding_id: uuid.UUID,
                           title: str, description: str,
                           severity: str, impact: str) -> str:
        uri = _risk_uri(risk_id)
        sev_individual = f"mat:{severity.capitalize()}"
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/maturity> {{
    <{uri}> a mat:Risk ;
             mat:hasTitle           "{_escape(title)}" ;
             mat:hasDescription     "{_escape(description)}" ;
             mat:hasSeverity        {sev_individual} ;
             mat:hasSeverityValue   "{severity}" ;
             mat:hasImpact          "{_escape(impact)}" ;
             mat:derivedFromFinding <{_finding_uri(finding_id)}> ;
             mat:pgId               "{risk_id}" .
  }}
}}
""")
        return uri

    # ── Queries ───────────────────────────────────────────────────────────────

    async def get_task_findings(self, task_id: uuid.UUID) -> list[dict]:
        task_uri = _task_uri(task_id)
        result = await self.query(f"""
SELECT ?finding ?description ?severity ?confidence ?approvalStatus
       ?evidence ?evidenceContent ?isInvalid
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?finding a aakp:Finding ;
             aakp:identifiedInTask   <{task_uri}> ;
             aakp:supportedByEvidence ?evidence .
    OPTIONAL {{ ?finding aakp:description    ?description }}
    OPTIONAL {{ ?finding aakp:hasConfidence  ?confidence }}
    OPTIONAL {{ ?finding aakp:approvalStatus ?approvalStatus }}
    OPTIONAL {{ ?finding mat:hasSeverity     ?severity }}
    OPTIONAL {{ ?finding aakp:isInvalid      ?isInvalid }}
    OPTIONAL {{ ?evidence aakp:content       ?evidenceContent }}
  }}
}}
ORDER BY DESC(?confidence)
""")
        return result.get("results", {}).get("bindings", [])

    async def get_assessment_graph(self, assessment_id: uuid.UUID) -> dict:
        assessment_uri = _assessment_uri(assessment_id)
        result = await self.query(f"""
SELECT DISTINCT ?s ?sType ?p ?o ?oType
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    {{
      ?s ?p ?o .
      ?s a ?sType .
      FILTER(?s = <{assessment_uri}>)
    }} UNION {{
      ?s ?p ?o .
      ?s a ?sType .
      ?s aakp:belongsToAssessment <{assessment_uri}> .
    }} UNION {{
      ?task aakp:belongsToAssessment <{assessment_uri}> .
      ?s ?p ?o .
      ?s a ?sType .
      ?s aakp:conductedForTask ?task .
    }} UNION {{
      ?task aakp:belongsToAssessment <{assessment_uri}> .
      ?interview aakp:conductedForTask ?task .
      ?s ?p ?o .
      ?s a ?sType .
      ?s aakp:askedInInterview ?interview .
    }} UNION {{
      ?task aakp:belongsToAssessment <{assessment_uri}> .
      ?interview aakp:conductedForTask ?task .
      ?question aakp:askedInInterview ?interview .
      ?s ?p ?o .
      ?s a ?sType .
      ?s aakp:answersQuestion ?question .
    }}
    OPTIONAL {{ ?o a ?oType }}
  }}
}}
LIMIT 4000
""")
        return result

    async def get_ontology_context(self, workstream: str, limit: int = 6) -> list[dict]:
        result = await self.query(f"""
SELECT ?class ?label ?comment
WHERE {{
  GRAPH <https://aakp.ai/graph/ontology> {{
    ?class a owl:Class .
    OPTIONAL {{ ?class rdfs:label ?label }}
    OPTIONAL {{ ?class rdfs:comment ?comment }}
    FILTER(
      CONTAINS(LCASE(STR(?class)), LCASE("{_escape(workstream)}"))
      || CONTAINS(LCASE(COALESCE(STR(?label), "")), LCASE("{_escape(workstream)}"))
      || CONTAINS(LCASE(COALESCE(STR(?comment), "")), LCASE("{_escape(workstream)}"))
    )
  }}
}}
LIMIT {limit}
""")
        return result.get("results", {}).get("bindings", [])

    async def get_agent_training_context(self, workstream: str, limit: int = 6) -> list[dict]:
        """Instance-level agent learning from the assessment knowledge graph."""
        agent_uri = _workstream_agent_uri(workstream)
        result = await self.query(f"""
SELECT ?ev ?type ?question ?answer ?content ?author ?mode ?filename ?concept ?conceptLabel
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    {{
      <{agent_uri}> aakp:hasTrainingEvent ?ev .
      ?ev a aakp:TrainingInteraction .
      BIND("TrainingInteraction" AS ?type)
      OPTIONAL {{ ?ev aakp:trainingQuestion ?question }}
      OPTIONAL {{ ?ev aakp:trainingAnswer ?answer }}
      OPTIONAL {{ ?ev aakp:answerAuthor ?author }}
      OPTIONAL {{ ?ev aakp:trainingMode ?mode }}
      OPTIONAL {{
        ?ev aakp:refersToConcept ?concept .
        OPTIONAL {{ ?concept arch:hasName ?conceptLabel }}
      }}
    }}
    UNION
    {{
      <{agent_uri}> aakp:hasAgentKnowledge ?ev .
      ?ev a aakp:AgentKnowledge .
      BIND("AgentKnowledge" AS ?type)
      OPTIONAL {{ ?ev aakp:knowledgeContent ?content }}
      OPTIONAL {{ ?ev aakp:knowledgeMode ?mode }}
      OPTIONAL {{ ?ev aakp:sourceFilename ?filename }}
      OPTIONAL {{
        ?ev aakp:refersToConcept ?concept .
        OPTIONAL {{ ?concept arch:hasName ?conceptLabel }}
      }}
    }}
  }}
}}
LIMIT {limit * 4}
""")
        return result.get("results", {}).get("bindings", [])

    @staticmethod
    def format_agent_training_context(bindings: list[dict]) -> str:
        if not bindings:
            return ""
        lines = ["Agent öğrenme kayıtları (Knowledge Graph):"]
        seen: set[str] = set()
        concepts_by_ev: dict[str, list[str]] = {}

        for row in bindings:
            ev = (row.get("ev") or {}).get("value", "")
            cl = (row.get("conceptLabel") or {}).get("value", "")
            if ev and cl and cl not in concepts_by_ev.get(ev, []):
                concepts_by_ev.setdefault(ev, []).append(cl)

        for row in bindings:
            ev = (row.get("ev") or {}).get("value", "")
            if not ev or ev in seen:
                continue
            seen.add(ev)
            kind = (row.get("type") or {}).get("value", "")
            concept_suffix = ""
            if concepts_by_ev.get(ev):
                concept_suffix = f" [kavram: {', '.join(concepts_by_ev[ev])}]"
            if kind == "TrainingInteraction":
                q = (row.get("question") or {}).get("value", "")
                a = (row.get("answer") or {}).get("value", "")
                author = (row.get("author") or {}).get("value", "consultant")
                lines.append(f"- [AAHA/{author}] S: {q[:200]} → C: {a[:300]}{concept_suffix}")
            else:
                content = (row.get("content") or {}).get("value", "")
                mode = (row.get("mode") or {}).get("value", "text")
                filename = (row.get("filename") or {}).get("value", "")
                label = filename or content[:120]
                lines.append(f"- [{mode}] {label}{concept_suffix}")
        return "\n".join(lines)

    async def get_gap_confidence(self) -> list[dict]:
        result = await self.query("""
SELECT ?gap ?gapTitle ?capabilityArea ?inferredConfidence
WHERE {
  GRAPH <https://aakp.ai/graph/maturity> {
    ?gap a mat:Gap .
    OPTIONAL { ?gap mat:hasTitle           ?gapTitle }
    OPTIONAL { ?gap mat:hasCapabilityArea  ?capabilityArea }
    OPTIONAL { ?gap mat:inferredConfidence ?inferredConfidence }
  }
}
ORDER BY DESC(?inferredConfidence)
""")
        return result.get("results", {}).get("bindings", [])

    async def get_finding_risk_chain(self, task_id: uuid.UUID) -> list[dict]:
        task_uri = _task_uri(task_id)
        result = await self.query(f"""
SELECT ?finding ?findingDesc ?confidence ?gap ?gapTitle ?risk ?riskTitle ?impact ?severity
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?finding a aakp:Finding ;
             aakp:identifiedInTask <{task_uri}> ;
             aakp:approvalStatus   "approved" .
    OPTIONAL {{ ?finding aakp:description  ?findingDesc }}
    OPTIONAL {{ ?finding aakp:hasConfidence ?confidence }}
  }}
  OPTIONAL {{
    GRAPH <https://aakp.ai/graph/maturity> {{
      ?finding mat:indicatesGap ?gap .
      OPTIONAL {{ ?gap mat:hasTitle ?gapTitle }}
      OPTIONAL {{
        ?risk mat:causedByGap ?gap ;
              a mat:Risk .
        OPTIONAL {{ ?risk mat:hasTitle        ?riskTitle }}
        OPTIONAL {{ ?risk mat:hasImpact       ?impact }}
        OPTIONAL {{ ?risk mat:hasSeverityValue ?severity }}
      }}
    }}
  }}
}}
ORDER BY DESC(?confidence)
""")
        return result.get("results", {}).get("bindings", [])

    # ── Inference Rules (S2-KA-003/004/005) ──────────────────────────────────

    async def run_inference_rules(self) -> dict[str, str]:
        results = {}
        if not _INFERENCE_DIR.exists():
            return {"error": f"Inference dir not found: {_INFERENCE_DIR}"}
        for rule_file in sorted(_INFERENCE_DIR.glob("rule_*.sparql")):
            sparql = rule_file.read_text(encoding="utf-8")
            # Strip comments before prefix block
            lines = [l for l in sparql.splitlines() if not l.strip().startswith("#")]
            clean = "\n".join(lines)
            try:
                await self.update(clean)
                results[rule_file.stem] = "ok"
            except Exception as e:
                results[rule_file.stem] = f"error: {e}"
        return results


    # ── Assessment-scoped named graphs (S2-KA-010) ───────────────────────────

    def _assessment_graph(self, assessment_id: uuid.UUID) -> str:
        """Named graph URI scoped to a single assessment for versioning."""
        return f"https://aakp.ai/graph/assessment/{assessment_id}"

    async def list_assessment_graphs(self) -> list[str]:
        """Return all per-assessment named graph URIs currently in Fuseki."""
        result = await self.query("""
SELECT DISTINCT ?g
WHERE {
  GRAPH ?g { ?s ?p ?o }
  FILTER(STRSTARTS(STR(?g), "https://aakp.ai/graph/assessment/"))
}
ORDER BY ?g
""")
        return [
            b["g"]["value"]
            for b in result.get("results", {}).get("bindings", [])
        ]

    async def copy_to_assessment_graph(self, assessment_id: uuid.UUID) -> str:
        """Copy all triples for an assessment from the shared graph into a
        per-assessment versioned named graph.

        Pattern:
          global  graph:assessment     — shared, live, all assessments
          scoped  graph:assessment/<id> — snapshot for this assessment only

        After copy the scoped graph can be exported, archived, or diffed.
        """
        src = "<https://aakp.ai/graph/assessment>"
        assessment_uri = str(_assessment_uri(assessment_id))
        dst = self._assessment_graph(assessment_id)

        await self.update(f"""
ADD GRAPH {src} TO GRAPH <{dst}> ;

DELETE {{
  GRAPH <{dst}> {{
    ?s ?p ?o
  }}
}}
WHERE {{
  GRAPH <{dst}> {{
    ?s ?p ?o
    FILTER NOT EXISTS {{
      {{
        ?s aakp:pgId "{assessment_id}" .
      }} UNION {{
        ?s aakp:belongsToAssessment <{assessment_uri}> .
      }} UNION {{
        ?s aakp:identifiedInTask ?task .
        <{assessment_uri}> aakp:hasTask ?task .
      }}
    }}
  }}
}}
""")
        return dst

    async def drop_assessment_graph(self, assessment_id: uuid.UUID) -> None:
        """Remove the per-assessment versioned named graph."""
        dst = self._assessment_graph(assessment_id)
        await self.update(f"DROP SILENT GRAPH <{dst}>")

    # ── Capability → Gap → Risk chain (S2-KA-009) ───────────────────────────

    async def get_capability_gap_risk_chain(
        self, capability_uri: str | None = None
    ) -> list[dict]:
        """Traverse Capability -> Gap -> Risk -> Finding chain across named graphs."""
        filter_clause = (
            f"FILTER(?capability = <{capability_uri}>)" if capability_uri else ""
        )
        result = await self.query(f"""
SELECT ?capability ?capabilityName
       ?gap ?gapTitle ?capabilityArea ?inferredConfidence
       ?risk ?riskTitle ?riskSeverity ?riskImpact
       ?finding ?findingDesc ?findingConfidence
WHERE {{
  GRAPH <https://aakp.ai/graph/architecture> {{
    ?capability a arch:Capability .
    OPTIONAL {{ ?capability arch:hasName ?capabilityName }}
  }}
  {filter_clause}

  GRAPH <https://aakp.ai/graph/maturity> {{
    ?gap a mat:Gap ;
         mat:affectsCapability ?capability .
    OPTIONAL {{ ?gap mat:hasTitle           ?gapTitle }}
    OPTIONAL {{ ?gap mat:hasCapabilityArea  ?capabilityArea }}
    OPTIONAL {{ ?gap mat:inferredConfidence ?inferredConfidence }}

    OPTIONAL {{
      ?risk a mat:Risk ;
            mat:causedByGap ?gap .
      OPTIONAL {{ ?risk mat:hasTitle         ?riskTitle }}
      OPTIONAL {{ ?risk mat:hasSeverityValue ?riskSeverity }}
      OPTIONAL {{ ?risk mat:hasImpact        ?riskImpact }}

      OPTIONAL {{
        ?risk mat:derivedFromFinding ?finding .
        GRAPH <https://aakp.ai/graph/assessment> {{
          OPTIONAL {{ ?finding aakp:description   ?findingDesc }}
          OPTIONAL {{ ?finding aakp:hasConfidence ?findingConfidence }}
        }}
      }}
    }}
  }}
}}
ORDER BY ?capability ?inferredConfidence DESC(?findingConfidence)
""")
        return result.get("results", {}).get("bindings", [])

    # ── Agent Registry (S3-AA-008) ───────────────────────────────────────────

    async def backfill_instance_labels(self) -> dict:
        """Add rdfs:label on KG individuals so Protege shows readable names."""
        try:
            await self.update("""
DELETE {
  GRAPH <https://aakp.ai/graph/assessment> { ?s rdfs:label ?old }
}
INSERT {
  GRAPH <https://aakp.ai/graph/assessment> { ?s rdfs:label ?label }
}
WHERE {
  GRAPH <https://aakp.ai/graph/assessment> {
    ?s a aakp:TrainingInteraction ;
       aakp:trainingQuestion ?q ;
       aakp:trainingMode ?m .
    BIND(CONCAT("[", ?m, "] ", SUBSTR(?q, 1, 100)) AS ?label)
    OPTIONAL { ?s rdfs:label ?old }
  }
}
""")
            await self.update("""
DELETE {
  GRAPH <https://aakp.ai/graph/assessment> { ?s rdfs:label ?old }
}
INSERT {
  GRAPH <https://aakp.ai/graph/assessment> { ?s rdfs:label ?label }
}
WHERE {
  GRAPH <https://aakp.ai/graph/assessment> {
    ?s a aakp:AgentKnowledge .
    OPTIONAL { ?s aakp:knowledgeMode ?mode }
    OPTIONAL { ?s aakp:sourceFilename ?fn }
    OPTIONAL { ?s aakp:knowledgeContent ?content }
    BIND(
      IF(
        BOUND(?fn),
        CONCAT("[", COALESCE(?mode, "text"), "] ", ?fn),
        CONCAT("[", COALESCE(?mode, "text"), "] ", SUBSTR(?content, 1, 100))
      ) AS ?label
    )
    OPTIONAL { ?s rdfs:label ?old }
  }
}
""")
            await self.update("""
DELETE {
  GRAPH <https://aakp.ai/graph/agents> { ?a rdfs:label ?old }
}
INSERT {
  GRAPH <https://aakp.ai/graph/agents> { ?a rdfs:label ?name }
}
WHERE {
  GRAPH <https://aakp.ai/graph/agents> {
    ?a a aakp:AssessmentAgent ; aakp:hasDisplayName ?name .
    OPTIONAL { ?a rdfs:label ?old }
  }
}
""")
            for ws, label in _WORKSTREAM_LABELS.items():
                uri = _workstream_agent_uri(ws)
                await self.update(f"""
DELETE {{
  GRAPH <https://aakp.ai/graph/assessment> {{ <{uri}> rdfs:label ?old }}
}}
INSERT {{
  GRAPH <https://aakp.ai/graph/assessment> {{ <{uri}> rdfs:label "{_escape(label)}" }}
}}
WHERE {{
  OPTIONAL {{
    GRAPH <https://aakp.ai/graph/assessment> {{ <{uri}> rdfs:label ?old }}
  }}
}}
""")
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def register_all_agents(self) -> dict:
        """Load agent registry SPARQL file and upsert all 8 agents into
        https://aakp.ai/graph/agents. Idempotent — INSERT DATA into named graph
        will overwrite existing triples on re-run thanks to SPARQL graph semantics."""
        try:
            bundled = Path(__file__).parent.parent / "sparql" / "agent_registry" / "register_agents.sparql"
            sparql_path = bundled if bundled.exists() else None
            if sparql_path is None or not sparql_path.exists():
                return {"status": "error", "detail": "Registry SPARQL file not found in bundle"}
            sparql = sparql_path.read_text(encoding="utf-8")
            lines = [l for l in sparql.splitlines() if not l.strip().startswith("#")]
            clean = "\n".join(lines)
            # Post raw SPARQL directly — file already contains all required PREFIX declarations.
            # Do NOT call self.update() which prepends _PREFIXES causing duplicate declarations.
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._update_url,
                    data={"update": clean},
                    auth=self._auth,
                    timeout=30,
                )
                resp.raise_for_status()
            return {"status": "ok", "graph": "https://aakp.ai/graph/agents"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def list_agents(self) -> list[dict]:
        """Return all registered assessment agents from the agents graph."""
        result = await self.query("""
SELECT ?agent ?agentId ?workstream ?displayName ?description ?isActive ?version
WHERE {
  GRAPH <https://aakp.ai/graph/agents> {
    ?agent a aakp:AssessmentAgent .
    OPTIONAL { ?agent aakp:hasAgentId     ?agentId }
    OPTIONAL { ?agent aakp:hasWorkstream  ?workstream }
    OPTIONAL { ?agent aakp:hasDisplayName ?displayName }
    OPTIONAL { ?agent aakp:hasDescription ?description }
    OPTIONAL { ?agent aakp:isActive       ?isActive }
    OPTIONAL { ?agent aakp:hasVersion     ?version }
  }
}
ORDER BY ?workstream
""")
        return result.get("results", {}).get("bindings", [])

    # ── SHACL Validation (S2-KA-002) ─────────────────────────────────────────

    async def validate_shacl(self, graph_uri: str | None = None) -> dict:
        """Validate Fuseki data against bundled SHACL shapes.

        Fuseki 5 SHACL endpoint: POST /dataset/shacl
        Body: concatenated Turtle shapes; optional ?graph= param for target graph.
        Returns: {"conforms": bool, "violations": [...], "shapes_loaded": [...]}
        """
        if not _SHACL_DIR.exists():
            return {"error": f"SHACL dir not found: {_SHACL_DIR}"}

        shape_files = sorted(_SHACL_DIR.glob("*.ttl"))
        if not shape_files:
            return {"error": "No SHACL shape files found"}

        combined = "\n\n".join(f.read_text(encoding="utf-8") for f in shape_files)
        shacl_url = f"{settings.fuseki_url}/{settings.fuseki_dataset}/shacl"
        params = {}
        if graph_uri:
            params["graph"] = graph_uri

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                shacl_url,
                content=combined.encode("utf-8"),
                params=params,
                headers={"Content-Type": "text/turtle", "Accept": "application/ld+json"},
                auth=self._auth,
                timeout=30,
            )
            resp.raise_for_status()
            report = resp.json()

        # Parse JSON-LD SHACL report: check sh:conforms
        conforms = True
        violations = []
        if isinstance(report, list):
            for node in report:
                conforms_vals = node.get("http://www.w3.org/ns/shacl#conforms", [])
                if conforms_vals and conforms_vals[0].get("@value") is False:
                    conforms = False
                for result in node.get("http://www.w3.org/ns/shacl#result", []):
                    if isinstance(result, dict) and "@id" in result:
                        violations.append(result["@id"])

        return {
            "conforms": conforms,
            "violations_count": len(violations),
            "violations": violations[:20],
            "shapes_loaded": [f.name for f in shape_files],
        }


    # ── Orchestrator SPARQL queries (S4-KA-002, S4-KA-003) ───────────────────

    def query_risk_heatmap(self) -> list[dict]:
        """Synchronous SPARQL query for risk heatmap (called from FastAPI sync context)."""
        import requests
        sparql_file = Path(__file__).parents[5] / "knowledge" / "sparql" / "orchestrator" / "02_risk_heatmap.sparql"
        bundled = Path(__file__).parent.parent / "sparql" / "orchestrator" / "02_risk_heatmap.sparql"
        path = bundled if bundled.exists() else sparql_file
        if not path.exists():
            return []
        query_text = path.read_text(encoding="utf-8")
        lines = [l for l in query_text.splitlines() if not l.strip().startswith("#")]
        resp = requests.get(
            self._query_url,
            params={"query": "\n".join(lines)},
            headers={"Accept": "application/sparql-results+json"},
            auth=self._auth,
            timeout=30,
        )
        if not resp.ok:
            return []
        bindings = resp.json().get("results", {}).get("bindings", [])
        return [
            {
                "capability_area": b.get("capabilityArea", {}).get("value", ""),
                "severity": b.get("severityLevel", {}).get("value", ""),
                "risk_count": int(b.get("riskCount", {}).get("value", 0)),
                "workstreams": b.get("affectedWorkstreams", {}).get("value", "").split(","),
                "max_confidence": float(b.get("maxConfidence", {}).get("value", 0) or 0),
            }
            for b in bindings
        ]

    def query_cross_task_dependencies(self) -> list[dict]:
        """Synchronous SPARQL query for cross-task dependencies (S4-KA-002)."""
        import requests
        sparql_file = Path(__file__).parents[5] / "knowledge" / "sparql" / "orchestrator" / "01_cross_task_dependencies.sparql"
        bundled = Path(__file__).parent.parent / "sparql" / "orchestrator" / "01_cross_task_dependencies.sparql"
        path = bundled if bundled.exists() else sparql_file
        if not path.exists():
            return []
        query_text = path.read_text(encoding="utf-8")
        lines = [l for l in query_text.splitlines() if not l.strip().startswith("#")]
        resp = requests.get(
            self._query_url,
            params={"query": "\n".join(lines)},
            headers={"Accept": "application/sparql-results+json"},
            auth=self._auth,
            timeout=30,
        )
        if not resp.ok:
            return []
        bindings = resp.json().get("results", {}).get("bindings", [])
        return [{k: v["value"] for k, v in b.items()} for b in bindings]


sparql_client = SPARQLClient()
