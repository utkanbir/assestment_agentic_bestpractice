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


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


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
                                 client_name: str, project_name: str) -> str:
        uri = _assessment_uri(assessment_id)
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Assessment ;
             aakp:hasClientName  "{_escape(client_name)}" ;
             aakp:hasProjectName "{_escape(project_name)}" ;
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


sparql_client = SPARQLClient()
