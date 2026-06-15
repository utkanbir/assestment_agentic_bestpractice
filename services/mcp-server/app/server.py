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
            findings_resp = await client.get(f"/api/v1/findings?task_id={task_id}")
            findings = findings_resp.json() if findings_resp.status_code == 200 else []
            covered_areas = {f.get("area") for f in findings if isinstance(f, dict)}
            suggestions = [q for q in KUBERNETES_QUESTION_BANK if q["area"] not in covered_areas]
            result = suggestions[0] if suggestions else {"text": "Tüm alanlar kapsandı. Interview tamamlanabilir.", "area": "complete"}
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

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
