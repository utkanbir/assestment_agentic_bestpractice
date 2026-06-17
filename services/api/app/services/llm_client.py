"""LLM client — interview intelligence (S11-BA-001/002/003)."""
import logging
import os

logger = logging.getLogger(__name__)

_MODEL_QUALITY = "claude-sonnet-4-6"
_MODEL_FAST = "claude-haiku-4-5-20251001"

WORKSTREAM_LABELS = {
    "kubernetes": "Kubernetes & Container Platformu",
    "cloud_strategy": "Bulut Stratejisi",
    "ingestion": "Veri Ingestion",
    "teradata_dr": "Teradata & DR",
    "lakehouse": "Lakehouse Mimarisi",
    "governance": "Veri Yönetişimi",
    "data_product": "Veri Ürünü",
    "cdp": "Müşteri Veri Platformu",
}

_FALLBACK_FOLLOWUP = (
    "Son yanıtınızı değerlendirdiğimde bazı noktalar dikkatimi çekti. "
    "Bu konuyu biraz daha açar mısınız — özellikle uygulama adımları ve karşılaştığınız zorluklar açısından?"
)


def _client():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=key)
    except Exception:
        return None


def generate_followup_question(
    workstream: str,
    questions_and_answers: list[dict],
    doc_context: str = "",
) -> str:
    """Generate a context-aware follow-up question using the interview history."""
    client = _client()
    if not client:
        return _FALLBACK_FOLLOWUP

    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)

    context_lines = []
    for qa in questions_and_answers[-6:]:
        q_text = qa.get("question", "")
        a_text = qa.get("answer", "").strip()
        context_lines.append(f"Soru: {q_text}")
        context_lines.append(f"Yanıt: {a_text if a_text else '(henüz yanıt verilmedi)'}")
    context = "\n".join(context_lines)

    doc_section = f"\n\nBu workstream için referans bilgiler:\n{doc_context}" if doc_context else ""

    prompt = f"""Sen {ws_label} konusunda uzman kıdemli bir danışmansın. Aşağıdaki interview konuşmasına dayanarak EN UYGUN takip sorusunu üret.

Konu: {ws_label}{doc_section}

Interview konuşması:
{context}

Görevin:
- Önceki yanıttaki eksik, belirsiz veya yüzeysel kalan noktayı tespit et
- O noktayı derinlemesine inceleyen TEK bir soru sor
- Soru ölçülebilir bir şey sormalı (sayı, yüzde, zaman, sorumlu kişi, araç adı gibi)
- Türkçe, soru işaretiyle bitmeli
- Yalnızca soruyu yaz, başka açıklama ekleme"""

    try:
        response = client.messages.create(
            model=_MODEL_QUALITY,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM follow-up generation failed: %s", exc)
        return _FALLBACK_FOLLOWUP


def evaluate_answer(
    workstream: str,
    question_text: str,
    answer_text: str,
    doc_context: str = "",
) -> str:
    """Evaluate an interview answer and return a structured assessment in Turkish."""
    client = _client()
    if not client:
        return "LLM değerlendirmesi için ANTHROPIC_API_KEY gerekli."

    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    doc_section = f"\n\nReferans bilgiler:\n{doc_context}" if doc_context else ""

    prompt = f"""Sen {ws_label} konusunda uzman bir değerlendiricisin.{doc_section}

Soru: {question_text}
Yanıt: {answer_text}

Bu yanıtı 3-4 cümleyle değerlendir:
1. Güçlü yanlar (varsa)
2. Eksik veya geliştirilebilecek noktalar
3. Olgunluk seviyesi: [Başlangıç / Gelişmekte / Olgun / İleri] — tek kelimeyle

Türkçe, direkt değerlendirme yaz. Giriş cümlesi kullanma."""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM evaluation failed: %s", exc)
        return "Değerlendirme sırasında hata oluştu."


def suggest_workstream_questions(
    workstream: str,
    existing_questions: list[str],
    count: int = 5,
    doc_context: str = "",
) -> list[str]:
    """Suggest new questions for a workstream's question bank."""
    client = _client()
    if not client:
        return []

    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    existing_str = "\n".join(f"- {q}" for q in existing_questions[:20])
    doc_section = f"\n\nReferans bilgiler:\n{doc_context}" if doc_context else ""

    prompt = f"""Sen {ws_label} konusunda uzman kıdemli bir danışmansın.{doc_section}

Mevcut soru bankası ({ws_label}):
{existing_str or "(henüz soru yok)"}

Bu listedeki soruları TEKRARLAMADAN, {count} adet yeni interview sorusu öner.
Her soru:
- Teknik derinlik veya süreç olgunluğunu ölçmeli
- Ölçülebilir yanıt beklentisi olmalı (sayı, araç, süre, kişi, oran)
- Türkçe, soru işaretiyle bitmeli
- Tek satır

Sadece soruları yaz, her biri ayrı satırda. Numara, tire, madde imi kullanma."""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        lines = [
            ln.strip().lstrip("•-*0123456789). ").strip()
            for ln in response.content[0].text.strip().splitlines()
            if ln.strip() and "?" in ln
        ]
        return lines[:count]
    except Exception as exc:
        logger.warning("LLM question suggestion failed: %s", exc)
        return []
