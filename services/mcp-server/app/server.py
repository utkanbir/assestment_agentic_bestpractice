import json
import uuid

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from app.config import settings
from app.kafka_producer import publish, stop_producer
from app.resources import KUBERNETES_QUESTION_BANK

server = Server("aakp-mcp")


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="resource://question_bank/kubernetes",
            name="Kubernetes Assessment Question Bank",
            description="K8s workstream için yapılandırılmış soru bankası (8 alan, 8 soru)",
            mimeType="application/json",
        ),
        Resource(
            uri="resource://current_task_findings",
            name="Current Task Findings",
            description="Aktif task için mevcut finding listesi (task_id query param ile)",
            mimeType="application/json",
        ),
        Resource(
            uri="resource://similar_findings",
            name="Similar Findings (Semantic Search)",
            description=(
                "Qdrant üzerinden semantik benzerlik araması. "
                "URI: resource://similar_findings?q=<metin>&limit=5&threshold=0.6"
            ),
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "resource://question_bank/kubernetes":
        return json.dumps(KUBERNETES_QUESTION_BANK, ensure_ascii=False, indent=2)

    if uri.startswith("resource://current_task_findings"):
        task_id = uri.split("?task_id=")[-1] if "?task_id=" in uri else None
        if not task_id:
            return json.dumps({"error": "task_id required: resource://current_task_findings?task_id=<uuid>"})
        async with httpx.AsyncClient(base_url=settings.api_base_url) as client:
            resp = await client.get(f"/api/v1/findings?task_id={task_id}")
            return resp.text

    # S2-BA-005: similar_findings resource — semantic search via Qdrant
    if uri.startswith("resource://similar_findings"):
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(uri.replace("resource://", "http://dummy/"))
        qs = parse_qs(parsed.query)
        query_text = qs.get("q", [""])[0]
        limit = int(qs.get("limit", ["5"])[0])
        threshold = float(qs.get("threshold", ["0.6"])[0])
        if not query_text:
            return json.dumps({"error": "q param required: resource://similar_findings?q=<metin>"})
        async with httpx.AsyncClient(base_url=settings.api_base_url) as client:
            resp = await client.post(
                "/api/v1/qdrant/search/findings",
                json={"query": query_text, "limit": limit, "score_threshold": threshold},
            )
            if resp.status_code == 200:
                return resp.text
            return json.dumps({"error": f"Qdrant search failed: {resp.status_code}"})

    return json.dumps({"error": f"Unknown resource: {uri}"})


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_finding",
            description="Bir interview'dan tespit edilen bulguyu kaydet. Evidence zorunludur (guardrail).",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task UUID"},
                    "evidence_id": {"type": "string", "description": "Evidence UUID (önceden add_evidence ile oluşturulmuş olmalı)"},
                    "description": {"type": "string", "description": "Finding açıklaması"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                },
                "required": ["task_id", "evidence_id", "description", "severity", "confidence"],
            },
        ),
        Tool(
            name="add_evidence",
            description="Interview cevabından elde edilen kanıtı kaydet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Kaynak (interviewee adı, doküman adı vb.)"},
                    "content": {"type": "string", "description": "Kanıt içeriği"},
                    "evidence_type": {"type": "string", "enum": ["interview", "document", "observation", "metric"]},
                    "interview_id": {"type": "string", "description": "Interview UUID (opsiyonel)"},
                },
                "required": ["source", "content", "evidence_type"],
            },
        ),
        Tool(
            name="suggest_next_question",
            description="Bağlam ve mevcut bulgulara göre sonraki soruyu öner.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interview_id": {"type": "string", "description": "Interview UUID"},
                    "context": {"type": "string", "description": "Son cevap ve bağlam özeti"},
                    "task_id": {"type": "string", "description": "Task UUID (mevcut bulgular için)"},
                    "area": {"type": "string", "description": "Odaklanılacak alan (opsiyonel)"},
                },
                "required": ["interview_id", "context", "task_id"],
            },
        ),
        Tool(
            name="get_similar_findings",
            description=(
                "Qdrant semantik vektör aramasıyla geçmiş assessment'lardan benzer bulgular getirir. "
                "Yeni bir bulgunun severity/confidence kalibrasyonu için kullan."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Aranacak bulgu/kanıt metni"},
                    "limit": {"type": "integer", "default": 5, "description": "Maksimum sonuç sayısı"},
                    "score_threshold": {"type": "number", "default": 0.6, "description": "Minimum cosine benzerlik skoru (0-1)"},
                    "severity_filter": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"], "description": "Opsiyonel severity filtresi"},
                },
                "required": ["text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient(base_url=settings.api_base_url) as client:

        if name == "add_evidence":
            resp = await client.post("/api/v1/evidences", json=arguments)
            resp.raise_for_status()
            evidence = resp.json()
            await publish("interview.answer.submitted", {
                "evidence_id": evidence["id"],
                "interview_id": arguments.get("interview_id"),
                "content": arguments["content"],
            })
            return [TextContent(type="text", text=json.dumps(evidence))]

        if name == "create_finding":
            resp = await client.post("/api/v1/findings", json=arguments)
            resp.raise_for_status()
            finding = resp.json()
            await publish("assessment.finding.created", {
                "finding_id": finding["id"],
                "task_id": arguments["task_id"],
                "severity": arguments["severity"],
                "confidence": arguments["confidence"],
            })
            return [TextContent(type="text", text=json.dumps(finding))]

        if name == "suggest_next_question":
            task_id = arguments["task_id"]
            workstream = arguments.get("area", "kubernetes")  # area param doubles as workstream hint

            # Pull question bank from API (S3-BA-004); fall back to hardcoded if unavailable
            bank_resp = await client.get(f"/api/v1/question-bank?workstream={workstream}")
            if bank_resp.status_code == 200 and bank_resp.json():
                bank = bank_resp.json()
            else:
                bank = [
                    {"area": q["area"], "text": q["text"], "follow_ups": q.get("follow_ups")}
                    for q in KUBERNETES_QUESTION_BANK
                ]

            findings_resp = await client.get(f"/api/v1/findings?task_id={task_id}")
            findings = findings_resp.json() if findings_resp.status_code == 200 else []
            covered_areas = {f.get("area") for f in findings if isinstance(f, dict)}
            suggestions = [q for q in bank if q.get("area") not in covered_areas]
            result = suggestions[0] if suggestions else {"text": "Tüm alanlar kapsandı. Interview tamamlanabilir.", "area": "complete"}
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        # S2-BA-004: semantic search tool
        if name == "get_similar_findings":
            payload = {
                "query": arguments["text"],
                "limit": arguments.get("limit", 5),
                "score_threshold": arguments.get("score_threshold", 0.6),
            }
            if arguments.get("severity_filter"):
                payload["severity_filter"] = arguments["severity_filter"]
            resp = await client.post("/api/v1/qdrant/search/findings", json=payload)
            if resp.status_code == 200:
                return [TextContent(type="text", text=resp.text)]
            return [TextContent(type="text", text=json.dumps({"error": f"Qdrant error: {resp.status_code}", "detail": resp.text}))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        try:
            await server.run(read_stream, write_stream, server.create_initialization_options())
        finally:
            await stop_producer()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
