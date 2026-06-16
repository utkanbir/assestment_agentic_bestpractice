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
