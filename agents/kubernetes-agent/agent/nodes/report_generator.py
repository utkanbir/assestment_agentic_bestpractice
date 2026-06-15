import json

from langchain_core.messages import SystemMessage

from agent.state import KubernetesAgentState


_SYSTEM = """Kubernetes assessment raporu yaz. Markdown formatında, Türkçe.
Bölümler: ## Özet | ## Bulgular | ## Riskler | ## Öneriler
Her bulgu için evidence bağlantısını belirt. Sadece onaylanan bulgular rapora girmeli."""


async def report_generator(state: KubernetesAgentState, llm) -> dict:
    findings = json.dumps(state.get("pending_findings", []), ensure_ascii=False, indent=2)
    scope = state.get("task_scope", "Kubernetes Assessment")

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=f"Kapsam: {scope}\n\nBulgular:\n{findings}"),
    ]

    response = await llm.ainvoke(messages)

    return {
        "report_markdown": response.content,
        "phase": "DONE",
    }
