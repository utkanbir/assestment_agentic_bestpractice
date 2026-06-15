import json

from langchain_core.messages import SystemMessage

from agent.state import KubernetesAgentState


_SYSTEM = """Kubernetes assessment raporu yaz. Markdown formatında, Türkçe.
Bölümler: ## Özet | ## Bulgular | ## Riskler | ## Kanıt Kalitesi | ## Öneriler
Her bulgu için evidence bağlantısını belirt. Sadece onaylanan bulgular rapora girmeli.
'Kanıt Kalitesi' bölümünde düşük güvenilirlikli gap'leri listele ve ek inceleme öner."""


async def report_generator(state: KubernetesAgentState, llm) -> dict:
    findings = json.dumps(state.get("pending_findings", []), ensure_ascii=False, indent=2)
    risks = json.dumps(state.get("generated_risks", []), ensure_ascii=False, indent=2)
    low_conf = json.dumps(state.get("low_confidence_gaps", []), ensure_ascii=False, indent=2)
    inference = json.dumps(state.get("inference_results", {}), ensure_ascii=False)
    scope = state.get("task_scope", "Kubernetes Assessment")

    messages = [
        SystemMessage(content=_SYSTEM),
        SystemMessage(content=(
            f"Kapsam: {scope}\n\n"
            f"Bulgular:\n{findings}\n\n"
            f"Türetilen Riskler:\n{risks}\n\n"
            f"Çıkarım Kuralları Sonucu: {inference}\n\n"
            f"Düşük Güvenilirlikli Gap'ler:\n{low_conf}"
        )),
    ]

    response = await llm.ainvoke(messages)

    return {
        "report_markdown": response.content,
        "phase": "DONE",
    }
