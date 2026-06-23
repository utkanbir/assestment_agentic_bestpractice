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


def _api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def _is_mock_key(key: str | None = None) -> bool:
    k = (key if key is not None else _api_key()).strip().lower()
    if not k:
        return True
    return (
        k.startswith("mock")
        or "placeholder" in k
        or k in ("test", "sk-ant-...", "sk-ant-")
    )


def llm_runtime_mode() -> str:
    """Return 'live' when Anthropic is configured, else 'mock'."""
    return "mock" if _is_mock_key() else "live"


def _extract_json_object(text: str) -> dict | None:
    import json
    import re

    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    blob = match.group()
    for candidate in (blob, blob.replace(""", '"').replace(""", '"')):
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


def _extract_json_array(text: str) -> list | None:
    import json
    import re

    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return None
    blob = match.group()
    for candidate in (blob, blob.replace(""", '"').replace(""", '"')):
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            continue
    return None


def _mock_simulated_answer(workstream: str, question_text: str, company_profile: dict | None) -> str:
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    profile_lines = []
    if company_profile:
        for key in ("industry", "size", "region", "name"):
            if company_profile.get(key):
                profile_lines.append(f"{key}: {company_profile[key]}")
    profile_section = "\n".join(profile_lines) if profile_lines else "Genel perakende kurumu"
    return (
        f"Kurumumuz {ws_label} alanında olgunluk çalışmalarını sürdürüyor. "
        f"Bu soruya özel olarak: mevcut süreçler dokümante edilmiş, ekip düzenli gözden geçirme yapıyor "
        f"ve iyileştirme backlog'u aktif yönetiliyor. ({profile_section})"
    )


_UNPROFESSIONAL_MARKERS = (
    "amk", "aq ", " aq", "sikt", "sikeyim", "orospu", "bok yemeye", "sk kafal", "sk kafalı",
    "salak", "aptal", "mal ",
)


def _client():
    key = _api_key()
    if _is_mock_key(key):
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=key)
    except Exception:
        return None


def _llm_error_message(exc: Exception, fallback: str) -> str:
    msg = str(exc).lower()
    if "credit balance is too low" in msg:
        return (
            "Anthropic API kredi bakiyesi yetersiz. "
            "console.anthropic.com → Plans & Billing üzerinden kredi yükleyin."
        )
    if "invalid x-api-key" in msg or "authentication" in msg or "invalid api key" in msg:
        return "Anthropic API anahtarı geçersiz. aakp-api-secret içindeki ANTHROPIC_API_KEY kontrol edin."
    if "rate_limit" in msg or "overloaded" in msg:
        return "Anthropic API geçici olarak yoğun. Birkaç dakika sonra tekrar deneyin."
    return fallback


def _mock_evaluate_answer(workstream: str, question_text: str, answer_text: str) -> str:
    """Deterministic local evaluation when LLM is unavailable (dev/mock key)."""
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    text = (answer_text or "").strip().lower()
    vague = any(w in text for w in ("bilmiyorum", "emin değil", "yok", "bilmiyoruz", "kararsız"))
    short = len(text) < 30
    if vague or short:
        maturity = "Başlangıç"
        gap = "Yanıt somut teknik detay (node sayısı, versiyon, mimari bileşenler) içermiyor."
    else:
        maturity = "Gelişmekte"
        gap = "Operasyonel pratikler, riskler ve ölçülebilir metrikler daha net açıklanabilir."
    return (
        f"{ws_label} — yerel AI değerlendirmesi: Yanıt soruyu {'yüzeysel' if vague or short else 'kısmen'} ele alıyor. "
        f"{gap} "
        f"Olgunluk seviyesi: {maturity}."
    )


def _mock_consultant_check(answer_text: str, consultant_comment: str) -> dict:
    comment = (consultant_comment or "").strip()
    if len(comment) < 8:
        return {
            "consistent": False,
            "feedback": "Yorum çok kısa; müşteri yanıtıyla ilişkisini açıklayın.",
        }
    comment_low = comment.lower()
    if any(marker in comment_low for marker in _UNPROFESSIONAL_MARKERS):
        return {
            "consistent": False,
            "feedback": (
                "Yerel kontrol (mock): Danışman yorumu profesyonel değil; "
                "mülakat ortamına uygun, yapıcı bir dil kullanın."
            ),
        }
    answer_low = (answer_text or "").strip().lower()
    vague_answer = any(w in answer_low for w in ("bilmiyorum", "emin değil", "yok"))
    if vague_answer and len(comment) >= 12:
        return {
            "consistent": True,
            "feedback": (
                "Yerel kontrol (mock): Müşteri yanıtı belirsiz; danışman yorumu yönlendirici görünüyor."
            ),
        }
    return {
        "consistent": True,
        "feedback": "Yerel kontrol (mock): Danışman yorumu müşteri yanıtıyla tutarlı görünüyor.",
    }


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
        return _mock_evaluate_answer(workstream, question_text, answer_text)

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
        if _is_mock_key():
            return _mock_evaluate_answer(workstream, question_text, answer_text)
        return _llm_error_message(exc, "Değerlendirme sırasında hata oluştu.")


_FALLBACK_AAHA = (
    "Bu workstream'deki mevcut mimari yaklaşımınızı ve karşılaştığınız en büyük operasyonel zorluğu "
    "somut örneklerle (araç adı, ekip büyüklüğü, SLA) açıklar mısınız?"
)


def generate_aaha_training_question(workstream: str, prior_events: list[dict] | None = None) -> str:
    """Generate an AAHA training question for consultant know-how capture."""
    client = _client()
    if not client:
        return _FALLBACK_AAHA

    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    prior_lines = []
    for ev in (prior_events or [])[-5:]:
        q = ev.get("question_text") or ""
        a = ev.get("answer_text") or ""
        if q and a:
            prior_lines.append(f"S: {q}\nC: {a}")
    prior_section = (
        f"\n\nDaha önce kaydedilen bilgiler:\n" + "\n---\n".join(prior_lines)
        if prior_lines else ""
    )

    prompt = f"""Sen {ws_label} konusunda uzman bir danışmansın. Bir junior agent'ı eğitmek için
danışmandan bilgi toplayan TEK bir soru üret.

Konu: {ws_label}{prior_section}

Kurallar:
- Önceki sorulardan farklı, derinlemesine bir bilgi sorusu sor
- Somut detay iste (araç, metrik, süreç adı, ekip yapısı)
- Türkçe, soru işaretiyle bitmeli
- Yalnızca soruyu yaz"""

    try:
        response = client.messages.create(
            model=_MODEL_QUALITY,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM AAHA question generation failed: %s", exc)
        return _FALLBACK_AAHA


def generate_aaha_training_answer(workstream: str, question_text: str) -> str:
    """Generate an expert AAHA training answer draft for consultant review."""
    client = _client()
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    fallback = (
        f"{ws_label} alanında bu konuda kurumsal best practice'ler uygulanıyor; "
        "süreçler dokümante, ekip düzenli gözden geçirme yapıyor ve "
        "iyileştirmeler backlog üzerinden takip ediliyor."
    )
    if not client:
        return fallback

    prompt = f"""Sen {ws_label} konusunda kıdemli bir danışmansın. Aşağıdaki eğitim sorusuna
uzmanlık bilgini aktaran somut bir yanıt yaz.

Soru: {question_text}

Kurallar:
- Türkçe, 4-6 cümle
- Araç adı, metrik, süreç ve ekip yapısı gibi somut detaylar kullan
- Junior agent'ın öğrenebileceği know-how odaklı yaz
- Yalnızca yanıt metnini yaz"""

    try:
        response = client.messages.create(
            model=_MODEL_QUALITY,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM AAHA answer generation failed: %s", exc)
        return fallback


def suggest_training_concept_ids(
    workstream: str,
    question_text: str,
    answer_text: str,
    candidates: list[dict],
    *,
    max_concepts: int = 3,
) -> list[str]:
    """Return concept id slugs (e.g. capability/container-platform) for refersToConcept."""
    from app.services.training_concepts import keyword_fallback_concept_ids

    if not candidates:
        return keyword_fallback_concept_ids(
            workstream, question_text, answer_text, max_concepts=max_concepts,
        )

    client = _client()
    if not client:
        return keyword_fallback_concept_ids(
            workstream, question_text, answer_text, max_concepts=max_concepts,
        )

    catalog_lines = "\n".join(
        f"- {c['id']}: {c['label']} ({c.get('description', '')})" for c in candidates
    )
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    prompt = f"""Sen {ws_label} domain uzmanısın. Aşağıdaki eğitim soru-yanıtını verilen kavram kataloğundan en fazla {max_concepts} kavramla eşle.

Soru: {question_text or '(metin bilgisi)'}
Yanıt: {answer_text}

Kavram kataloğu (yalnızca bu id'leri kullan):
{catalog_lines}

Yanıtı YALNIZCA JSON olarak ver:
{{"concept_ids": ["capability/...", "theme/..."]}}"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_json_object(response.content[0].text.strip())
        if data and isinstance(data.get("concept_ids"), list):
            ids = [str(x) for x in data["concept_ids"] if isinstance(x, str)]
            if ids:
                return ids[:max_concepts]
    except Exception as exc:
        logger.warning("LLM concept linking failed: %s", exc)

    return keyword_fallback_concept_ids(
        workstream, question_text, answer_text, max_concepts=max_concepts,
    )


def generate_simulated_answer(
    workstream: str,
    question_text: str,
    company_profile: dict | None = None,
) -> str:
    """Generate a realistic simulated interview answer for autonomous assessment."""
    client = _client()
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    profile_lines = []
    if company_profile:
        for key in ("industry", "size", "region", "name"):
            if company_profile.get(key):
                profile_lines.append(f"{key}: {company_profile[key]}")
    profile_section = "\n".join(profile_lines) if profile_lines else "Genel perakende kurumu"

    if not client:
        return _mock_simulated_answer(workstream, question_text, company_profile)

    prompt = f"""Sen {ws_label} konusunda deneyimli bir IT liderisin. Aşağıdaki interview sorusuna kurum adına gerçekçi bir yanıt ver.

Kurum profili:
{profile_section}

Soru: {question_text}

Kurallar:
- Türkçe, 3-5 cümle
- Somut örnekler (araç adı, süre, ekip, metrik) kullan
- Abartma; orta-ileri olgunluk seviyesinde cevap ver
- Yalnızca yanıt metnini yaz"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM simulated answer failed: %s", exc)
        return (
            f"{ws_label} kapsamında standart süreçlerimiz uygulanıyor; "
            "dokümantasyon ve periyodik gözden geçirme mevcut."
        )


def generate_simulated_answers_batch(
    workstream: str,
    question_texts: list[str],
    company_profile: dict | None = None,
) -> list[str]:
    """Generate simulated answers for all questions in a workstream via one LLM call."""
    if not question_texts:
        return []

    client = _client()
    if not client:
        return [
            _mock_simulated_answer(workstream, q, company_profile)
            for q in question_texts
        ]

    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)
    profile_lines = []
    if company_profile:
        for key in ("industry", "size", "region", "name"):
            if company_profile.get(key):
                profile_lines.append(f"{key}: {company_profile[key]}")
    profile_section = "\n".join(profile_lines) if profile_lines else "Genel perakende kurumu"

    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(question_texts))
    n = len(question_texts)
    max_tokens = min(4096, max(400, 400 * n))

    prompt = f"""Sen {ws_label} konusunda deneyimli bir IT liderisin. Kurum adına aşağıdaki {n} interview sorusuna gerçekçi yanıtlar ver.

Kurum profili:
{profile_section}

Sorular:
{numbered}

Kurallar:
- Her soru için Türkçe, 3-5 cümle yanıt
- Somut örnekler (araç adı, süre, ekip, metrik) kullan
- Abartma; orta-ileri olgunluk seviyesinde cevap ver
- YALNIZCA JSON array döndür: soru sırasıyla aynı sırada {n} string eleman
- Örnek format: ["yanıt1", "yanıt2", ...]"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parsed = _extract_json_array(response.content[0].text.strip())
        if parsed and len(parsed) == n:
            return [str(a).strip() for a in parsed]
        logger.warning(
            "Batch simulated answers parse mismatch: expected %d, got %s",
            n, len(parsed) if parsed else 0,
        )
    except Exception as exc:
        logger.warning("LLM batch simulated answers failed: %s", exc)

    return [
        generate_simulated_answer(workstream, q, company_profile)
        for q in question_texts
    ]


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


def chat_assistant_reply(
    workstream: str,
    user_message: str,
    doc_context: str = "",
    ontology_context: str = "",
    history: list[dict] | None = None,
    platform_context: str = "",
    product_context: str = "",
) -> str:
    """Generate assistant response with optional multi-turn history (S18/S19)."""
    from app.services.chat_platform import try_direct_platform_answer

    client = _client()
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream) if workstream != "general" else "Genel"

    if not client:
        if product_context.strip() and "Active questions total:" in product_context:
            total_line = product_context.split("Active questions total:")[-1].split("\n")[0].strip()
            return (
                f"Question Bank data product port'undan okundu: {total_line} aktif soru."
            )
        direct = try_direct_platform_answer(user_message, platform_context)
        if direct:
            return direct
        return (
            f"{ws_label} sohbeti için mesajınızı aldım. "
            "Bu ortamda ANTHROPIC_API_KEY tanımlı olmadığı için kısa bir yerel yanıt döndüm."
            + (f" {platform_context}" if platform_context else "")
        )

    context_blocks = []
    if product_context.strip():
        context_blocks.append(f"Data product (birincil kaynak):\n{product_context}")
    if platform_context.strip():
        context_blocks.append(f"Platform bilgisi:\n{platform_context}")
    if doc_context.strip():
        context_blocks.append(f"Dokuman baglami:\n{doc_context}")
    if ontology_context.strip():
        context_blocks.append(f"Ontoloji baglami:\n{ontology_context}")
    merged_context = "\n\n".join(context_blocks) if context_blocks else "Ek baglam yok."

    system_rules = f"""Sen AAKP icin calisan bir degerlendirme asistansin.
Kapsam: {ws_label}

Baglam:
{merged_context}

Kurallar:
- Turkce cevap ver
- "Data product" blogu varsa onu birincil kaynak say; raw tablo veya tahmin kullanma
- Platform bilgisindeki sayilari oldugu gibi kullan
- "Assessment Results View" data product verisi varsa onu birincil kaynak say
- Kisa, uygulanabilir ve maddeli ol
- Emin olmadigin yerde varsayimini belirt
- En fazla 6 cumle/madde kullan
"""

    messages: list[dict] = []
    for msg in (history or [])[-12:]:
        role = msg.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=500,
            system=system_rules,
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("LLM chat response failed: %s", exc)
        return "Yanıt üretimi sırasında geçici bir hata oluştu. Lütfen tekrar deneyin."


_MODE_INSTRUCTIONS = {
    "rewrite": "Metni yeniden yaz.",
    "expand": "Metni genişlet ve daha fazla detay ekle.",
    "shorten": "Metni kısalt, öz tut.",
    "tone_executive": "Metni yönetici diline çevir — kısa, stratejik, karar odaklı.",
}


def report_section_ai_edit(
    section_type: str,
    content: str,
    instruction: str,
    mode: str = "rewrite",
) -> str:
    """S18: AI-edit a report section body or table rows."""
    client = _client()
    mode_hint = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["rewrite"])
    if not client:
        if section_type == "text" and content.strip():
            return f"{content.strip()}\n\n[AI düzenleme — ANTHROPIC_API_KEY yok]"
        return content

    format_hint = (
        "Yalnızca düzenlenmiş metni döndür, başka açıklama ekleme."
        if section_type == "text"
        else "Yalnızca JSON array of arrays (tablo satırları) döndür."
    )
    prompt = f"""Sen bir danışmanlık raporu editörüsün.

Bölüm tipi: {section_type}
Mod: {mode_hint}
Ek talimat: {instruction}

Mevcut içerik:
{content}

{format_hint}"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if section_type == "table":
            start = text.find("[")
            end = text.rfind("]")
            if start >= 0 and end > start:
                return text[start : end + 1]
        return text
    except Exception as exc:
        logger.warning("Report AI edit failed: %s", exc)
        return content


def report_section_ai_generate(
    section_type: str,
    section_title: str,
    section_data: str,
    assessment_context: str,
    instruction: str = "Bu bölüm için profesyonel rapor metni yaz",
    mode: str = "generate",
) -> str:
    """S20: Generate report section content from assessment context."""
    client = _client()
    mode_hint = _MODE_INSTRUCTIONS.get(mode, "Yeni içerik üret.")

    if section_type == "text":
        output_hint = "Yalnızca Türkçe rapor paragrafını döndür (2-5 cümle)."
    elif section_type == "table":
        output_hint = "Yalnızca JSON array of arrays (tablo satırları) döndür. Sütun sayısını koru."
    elif section_type in ("chart_radar", "chart_heatmap", "kpi_grid"):
        output_hint = "Yalnızca 2-4 cümlelik Türkçe yorum metni döndür (commentary)."
    elif section_type == "cover":
        output_hint = "Yalnızca tek satırlık Türkçe alt başlık (subtitle) döndür."
    else:
        output_hint = "Yalnızca Türkçe kısa açıklama döndür."

    if not client:
        return ""

    prompt = f"""Sen kıdemli bir danışmanlık raporu yazarısın.

Assessment bağlamı:
{assessment_context}

Bölüm: {section_title}
Bölüm tipi: {section_type}
Mod: {mode_hint}
Talimat: {instruction}

Mevcut bölüm verisi:
{section_data[:3000]}

{output_hint}"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if section_type == "table":
            start = text.find("[")
            end = text.rfind("]")
            if start >= 0 and end > start:
                return text[start : end + 1]
        return text
    except Exception as exc:
        logger.warning("Report AI generate failed: %s", exc)
        return ""


def generate_consultant_synthesis(qa_items: list[dict]) -> str:
    """Blend Q&A evaluations and consultant comments into a batch summary."""
    client = _client()
    lines = []
    for item in qa_items:
        block = [
            f"[{item.get('workstream', '')}] Soru: {item.get('question', '')}",
            f"Yanıt: {item.get('answer', '')}",
        ]
        if item.get("evaluation"):
            block.append(f"Agent değerlendirmesi: {item['evaluation']}")
        if item.get("consultant_comment"):
            name = item.get("consultant_name") or "Danışman"
            block.append(f"{name} yorumu: {item['consultant_comment']}")
        lines.append("\n".join(block))

    context = "\n\n---\n\n".join(lines[:40])
    if not client:
        return (
            "Toplu değerlendirme özeti (mock):\n\n"
            + "\n".join(f"- {i.get('workstream')}: {i.get('evaluation', '')[:120]}" for i in qa_items[:5])
        )

    prompt = f"""Sen kıdemli IT assessment danışmanısın. Aşağıdaki interview Q&A kayıtlarını, agent değerlendirmelerini ve danışman yorumlarını birleştirerek Türkçe toplu bir değerlendirme özeti yaz.

Kurallar:
- 4-6 paragraf
- Workstream bazında temel bulguları grupla
- Danışman yorumlarını öne çıkar
- Yönetici özeti tonu

Veriler:
{context}"""

    try:
        response = client.messages.create(
            model=_MODEL_QUALITY,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("Consultant synthesis failed: %s", exc)
        return "Toplu değerlendirme oluşturulamadı."


def suggest_maturity_score(
    workstream: str,
    evaluations: list[dict],
    findings: list[dict],
) -> dict:
    """Suggest maturity score, level, and notes from evaluations + findings."""
    client = _client()
    ws_label = WORKSTREAM_LABELS.get(workstream, workstream)

    eval_text = "\n".join(
        f"- Soru: {e.get('question', '')}\n  Değerlendirme: {e.get('evaluation', '')[:200]}"
        for e in evaluations[:15]
    ) or "(değerlendirme yok)"
    finding_text = "\n".join(
        f"- [{f.get('severity')}] {f.get('description', '')[:150]}"
        for f in findings[:10]
    ) or "(bulgu yok)"

    if not client:
        score = min(5.0, max(1.0, 2.5 + len(evaluations) * 0.1 - len(findings) * 0.2))
        level = "developing" if score < 3 else "defined"
        return {
            "score": round(score, 1),
            "maturity_level": level,
            "notes": f"{ws_label} için otomatik öneri (mock): {len(evaluations)} değerlendirme, {len(findings)} bulgu.",
        }

    prompt = f"""Sen {ws_label} olgunluk değerlendirme uzmanısın.

Interview değerlendirmeleri:
{eval_text}

Bulgular:
{finding_text}

JSON formatında yanıt ver (başka metin ekleme):
{{"score": <0-5 ondalık>, "maturity_level": "<initial|developing|defined|managed|optimizing>", "notes": "<Türkçe 2-3 cümle gerekçe>"}}"""

    try:
        import json
        import re
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "score": float(data.get("score", 2.5)),
                "maturity_level": str(data.get("maturity_level", "developing")),
                "notes": str(data.get("notes", "")),
            }
    except Exception as exc:
        logger.warning("Maturity AI suggest failed: %s", exc)

    return {
        "score": 2.5,
        "maturity_level": "developing",
        "notes": f"{ws_label} için AI önerisi oluşturulamadı.",
    }


def generate_recommendation_for_finding(
    finding_description: str,
    severity: str,
    workstream: str = "",
) -> dict:
    """Generate actionable recommendation text from an approved finding."""
    client = _client()
    sev = severity or "medium"
    priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5}
    priority = priority_map.get(sev, 3)
    effort = "high" if sev in ("critical", "high") else "medium"

    if not client:
        return {
            "description": (
                f"[{sev.upper()}] {finding_description[:200]} için somut iyileştirme aksiyonu tanımlayın "
                f"({workstream or 'genel'} workstream)."
            ),
            "priority": priority,
            "effort": effort,
        }

    prompt = f"""Sen IT dönüşüm danışmanısın. Aşağıdaki onaylanmış bulgu için TEK somut öneri yaz.

Workstream: {workstream or 'genel'}
Önem: {sev}
Bulgu: {finding_description}

JSON formatında yanıt ver (başka metin ekleme):
{{"description": "<Türkçe, eylem odaklı öneri>", "priority": <1-5>, "effort": "<low|medium|high>"}}"""

    try:
        import json
        import re

        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "description": str(data.get("description", finding_description)),
                "priority": int(data.get("priority", priority)),
                "effort": str(data.get("effort", effort)),
            }
    except Exception as exc:
        logger.warning("Recommendation generation failed: %s", exc)

    return {
        "description": f"{finding_description[:180]} — iyileştirme planı oluşturulmalı.",
        "priority": priority,
        "effort": effort,
    }


def check_consultant_comment_consistency(
    section_title: str,
    section_content: str,
    consultant_comment: str,
) -> dict:
    """AI consistency check between report section and consultant comment."""
    comment = (consultant_comment or "").strip()
    if not comment:
        return {"consistent": True, "feedback": "Danışman yorumu boş — tutarlılık kontrolü atlandı."}

    client = _client()
    if not client:
        consistent = len(comment) >= 10
        return {
            "consistent": consistent,
            "feedback": (
                "Danışman yorumu kaydedildi (mock kontrol)."
                if consistent
                else "Yorum çok kısa; bölüm içeriğiyle ilişkisini açıklayın."
            ),
        }

    prompt = f"""Sen rapor kalite kontrol uzmanısın. Rapor bölümü ile danışman yorumunun tutarlılığını değerlendir.

Bölüm başlığı: {section_title}
Bölüm içeriği:
{section_content[:2500]}

Danışman yorumu:
{comment[:2000]}

JSON formatında yanıt ver:
{{"consistent": <true|false>, "feedback": "<Türkçe kısa geri bildirim — tutarsızlık varsa belirt>"}}"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_json_object(response.content[0].text.strip())
        if data:
            return {
                "consistent": bool(data.get("consistent", True)),
                "feedback": str(data.get("feedback", "Kontrol tamamlandı.")),
            }
        logger.warning("Consultant comment check: JSON parse failed")
    except Exception as exc:
        logger.warning("Consultant comment check failed: %s", exc)
        return {
            "consistent": True,
            "feedback": _llm_error_message(exc, "AI kontrolü tamamlanamadı; yorum kaydedildi."),
        }

    return {"consistent": True, "feedback": "AI kontrolü tamamlanamadı; yorum kaydedildi."}


def check_answer_consultant_consistency(
    question_text: str,
    answer_text: str,
    consultant_comment: str,
) -> dict:
    """AI consistency check between interview Q&A and consultant comment."""
    comment = (consultant_comment or "").strip()
    if not comment:
        return {"consistent": True, "feedback": "Danışman yorumu boş — tutarlılık kontrolü atlandı."}

    client = _client()
    if not client:
        return _mock_consultant_check(answer_text, comment)

    prompt = f"""Sen mülakat kalite kontrol uzmanısın. Soru, müşteri yanıtı ve danışman yorumunun tutarlılığını değerlendir.

Soru:
{question_text[:1500]}

Müşteri yanıtı:
{answer_text[:2000]}

Danışman yorumu:
{comment[:2000]}

JSON formatında yanıt ver:
{{"consistent": <true|false>, "feedback": "<Türkçe kısa geri bildirim — tutarsızlık varsa belirt>"}}"""

    try:
        response = client.messages.create(
            model=_MODEL_FAST,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_json_object(response.content[0].text.strip())
        if data:
            return {
                "consistent": bool(data.get("consistent", True)),
                "feedback": str(data.get("feedback", "Kontrol tamamlandı.")),
            }
        logger.warning("Answer consultant check: JSON parse failed")
    except Exception as exc:
        logger.warning("Answer consultant check failed: %s", exc)
        if _is_mock_key():
            return _mock_consultant_check(answer_text, comment)
        return {
            "consistent": True,
            "feedback": _llm_error_message(exc, "AI kontrolü tamamlanamadı; yorum kaydedildi."),
        }

    return {"consistent": True, "feedback": "AI kontrolü tamamlanamadı; yorum kaydedildi."}
