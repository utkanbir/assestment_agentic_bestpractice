"""S19: Rule-based Turkish EXPLAIN PLAN narrative from layer touch steps."""
from app.schemas.architecture import LayerTouchOut

_LAYER_LABELS = {
    "information": "Information",
    "knowledge": "Knowledge",
    "agent": "Agent",
    "data": "Data",
}

_TECH_LABELS = {
    "postgresql": "PostgreSQL",
    "qdrant": "Qdrant",
    "fuseki": "Fuseki SPARQL",
    "claude": "Claude",
    "minio": "MinIO",
    "kafka": "Kafka",
}


def _step_sentence(step: LayerTouchOut) -> str:
    layer = _LAYER_LABELS.get(step.layer, step.layer)
    tech = _TECH_LABELS.get(step.technology, step.technology)
    detail = step.detail or {}
    ws = detail.get("workstream", "general")
    action = step.action

    if step.layer == "knowledge" and step.technology == "fuseki" and action == "read":
        hits = detail.get("hits", 0)
        if detail.get("status") == "unavailable":
            return (
                f"Knowledge katmanında Fuseki ontoloji servisine erişmeye çalıştık; "
                f"bu adımda bağlam okunamadı."
            )
        return (
            f"Knowledge katmanında Fuseki SPARQL endpoint'inden {ws} ontolojisi okundu; "
            f"amaç sorudaki domain kavramlarına bağlam sağlamaktı ({hits} kavram kaydı)."
        )

    if step.layer == "information" and step.technology == "qdrant" and action == "search":
        chunks = detail.get("chunks", 0)
        if detail.get("status") == "unavailable":
            return (
                "Information katmanında Qdrant vektör araması denendi ancak servis bu adımda kullanılamadı."
            )
        return (
            f"Information katmanında Qdrant üzerinde semantik arama yapıldı; "
            f"{chunks} ilgili doküman parçası bulundu."
        )

    if step.layer == "information" and step.technology == "postgresql" and action == "write":
        role = detail.get("role", "mesaj")
        table = detail.get("table", "chat_messages")
        return (
            f"Information katmanında {tech} veritabanındaki {table} tablosuna "
            f"{role} kaydı yazıldı."
        )

    if step.layer == "agent" and step.technology == "claude" and action == "infer":
        return (
            "Agent katmanında Claude modeli çağrılarak kullanıcı isteğine uygun nihai yanıt üretildi."
        )

    return (
        f"{layer} katmanında {tech} üzerinde '{action}' işlemi gerçekleştirildi."
    )


def build_narrative(steps: list[LayerTouchOut], operation: str = "") -> str:
    if not steps:
        return "Bu işlem için kayıtlı katman adımı bulunamadı."

    ordered = sorted(
        steps,
        key=lambda s: (s.step_order if s.step_order is not None else 999, s.created_at),
    )
    sentences = [_step_sentence(s) for s in ordered]

    intro = "Bu isteği yanıtlamak için sistem aşağıdaki katman akışını izledi."
    if operation:
        intro = f"'{operation}' işlemini yanıtlamak için sistem aşağıdaki katman akışını izledi."

    body = " ".join(sentences)
    return f"{intro} {body}"
