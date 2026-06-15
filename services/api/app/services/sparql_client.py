import uuid
from string import Template

import httpx

from app.core.config import settings

_PREFIXES = """
PREFIX aakp: <https://aakp.ai/ontology/assessment#>
PREFIX mat:  <https://aakp.ai/ontology/maturity#>
PREFIX arch: <https://aakp.ai/ontology/architecture#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

_DATA_NS = "https://aakp.ai/data"


def _task_uri(task_id: uuid.UUID) -> str:
    return f"{_DATA_NS}/task/{task_id}"


def _finding_uri(finding_id: uuid.UUID) -> str:
    return f"{_DATA_NS}/finding/{finding_id}"


def _evidence_uri(evidence_id: uuid.UUID) -> str:
    return f"{_DATA_NS}/evidence/{evidence_id}"


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

    async def get_task_findings(self, task_id: uuid.UUID) -> list[dict]:
        task_uri = _task_uri(task_id)
        result = await self.query(f"""
SELECT ?finding ?description ?severity ?confidence ?approvalStatus
       ?evidence ?evidenceContent
WHERE {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    ?finding a aakp:Finding ;
             aakp:identifiedInTask   <{task_uri}> ;
             aakp:supportedByEvidence ?evidence .
    OPTIONAL {{ ?finding aakp:description    ?description }}
    OPTIONAL {{ ?finding aakp:hasConfidence  ?confidence }}
    OPTIONAL {{ ?finding aakp:approvalStatus ?approvalStatus }}
    OPTIONAL {{ ?finding mat:hasSeverity     ?severity }}
    OPTIONAL {{ ?evidence aakp:content       ?evidenceContent }}
  }}
}}
ORDER BY DESC(?confidence)
""")
        return result.get("results", {}).get("bindings", [])

    async def insert_evidence(self, evidence_id: uuid.UUID, interview_id: uuid.UUID | None,
                               source: str, content: str) -> str:
        uri = _evidence_uri(evidence_id)
        interview_triple = f'<{uri}> aakp:collectedInInterview <{_DATA_NS}/interview/{interview_id}> .' if interview_id else ""
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:InterviewEvidence ;
             aakp:hasSource "{source}" ;
             aakp:content   "{content}" ;
             aakp:pgId      "{evidence_id}" .
    {interview_triple}
  }}
}}
""")
        return uri

    async def insert_finding(self, finding_id: uuid.UUID, task_id: uuid.UUID,
                              evidence_id: uuid.UUID, description: str,
                              severity: str, confidence: float) -> str:
        uri = _finding_uri(finding_id)
        sev_uri = f"mat:{severity.capitalize()}"
        await self.update(f"""
INSERT DATA {{
  GRAPH <https://aakp.ai/graph/assessment> {{
    <{uri}> a aakp:Finding ;
             aakp:identifiedInTask    <{_task_uri(task_id)}> ;
             aakp:supportedByEvidence <{_evidence_uri(evidence_id)}> ;
             aakp:description         "{description}" ;
             mat:hasSeverity          {sev_uri} ;
             aakp:hasConfidence       "{confidence}"^^xsd:decimal ;
             aakp:approvalStatus      "pending" ;
             aakp:pgId                "{finding_id}" .
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


sparql_client = SPARQLClient()
