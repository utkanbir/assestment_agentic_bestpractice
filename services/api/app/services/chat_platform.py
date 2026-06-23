"""S19/S29: Platform facts and assessment data product context for chat."""

import uuid



from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession



from app.models.assessment import Assessment





RESULTS_QUERY_TRIGGERS = (

    "sonuç",

    "sonuc",

    "özet",

    "ozet",

    "bulgu",

    "olgunluk",

    "değerlendir",

    "degerlendir",

    "göster",

    "goster",

    "rapor",

    "kpi",

    "workstream",

    "assessment",

    "maturity",

    "heatmap",

    "risk",

)





async def build_platform_context(

    db: AsyncSession,

    assessment_id: uuid.UUID | None = None,

    include_results: bool = False,

) -> str:

    count_result = await db.execute(select(func.count()).select_from(Assessment))

    total = count_result.scalar() or 0

    lines = [f"Toplam assessment sayısı: {total}"]



    if assessment_id:

        assessment = await db.get(Assessment, assessment_id)

        if assessment:

            lines.append(

                f"Seçili assessment: {assessment.client_name} — {assessment.project_name} "

                f"(durum: {assessment.status})"

            )

            if include_results:

                from app.services.assessment_results_product import (

                    compose_assessment_results_view,

                    format_assessment_results_for_llm,

                )



                try:

                    view = await compose_assessment_results_view(assessment_id, db)

                    lines.append(format_assessment_results_for_llm(view))

                except ValueError:

                    lines.append("Assessment Results View: kayıt bulunamadı.")

    return "\n".join(lines)





def should_include_assessment_results(user_message: str) -> bool:

    msg = user_message.lower()

    return any(t in msg for t in RESULTS_QUERY_TRIGGERS)





def try_direct_platform_answer(user_message: str, platform_context: str) -> str | None:

    """Return a direct answer for common platform questions when LLM is unavailable."""

    msg = user_message.lower()

    count_triggers = (

        "kaç assessment",

        "kac assessment",

        "assessment sayısı",

        "assessment sayisi",

        "assessment var",

        "kaç tane assessment",

    )

    if any(t in msg for t in count_triggers):

        for line in platform_context.splitlines():

            if line.startswith("Toplam assessment"):

                return f"Platformda {line.split(':', 1)[-1].strip()} assessment kaydı bulunuyor."



    if should_include_assessment_results(user_message) and "Assessment Results View" in platform_context:

        # Return the formatted block after the header line

        idx = platform_context.find("=== Assessment Results View")

        if idx >= 0:

            return platform_context[idx:][:3500]

    return None


