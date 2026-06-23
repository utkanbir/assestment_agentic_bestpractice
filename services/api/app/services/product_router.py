"""Agent product router (prototype): KG/catalog → contract → port.

First intent: question count via Question Bank data product.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question_bank import WorkstreamQuestion
from app.services.assessment_results_product import load_data_products_catalog
from app.services.llm_client import WORKSTREAM_LABELS

QUESTION_BANK_PRODUCT_ID = "question_bank"

QUESTION_COUNT_TRIGGERS = (
    "kaç soru",
    "kac soru",
    "soru sayısı",
    "soru sayisi",
    "soru tanımlı",
    "soru tanimli",
    "tanımlı soru",
    "tanimli soru",
    "question bank",
    "soru bankası",
    "soru bankasi",
    "kaç tane soru",
    "kac tane soru",
)

# Ontology-aligned concept hints (KG reasoning step, keyword phase)
QUESTION_ONTOLOGY_HINTS = ("soru", "question", "question bank", "soru bank")


@dataclass
class ProductRouteResult:
    intent: str
    product_id: str
    product_name: str
    workstream: str | None
    port: str
    contract_summary: str
    om_contract_note: str | None
    total_active: int
    by_workstream: dict[str, int]
    reasoning_steps: list[str] = field(default_factory=list)

    def format_for_llm(self) -> str:
        ws_lines = "\n".join(f"  - {ws}: {n}" for ws, n in sorted(self.by_workstream.items()))
        om_line = f"\nOpenMetadata contract note: {self.om_contract_note}" if self.om_contract_note else ""
        return (
            f"=== Data Product Router ===\n"
            f"Intent: {self.intent}\n"
            f"Resolved product: {self.product_name} ({self.product_id})\n"
            f"Reasoning steps:\n"
            + "\n".join(f"  - {s}" for s in self.reasoning_steps)
            + f"\nCatalog contract: {self.contract_summary}\n"
            f"Port invoked: {self.port}\n"
            f"Active questions total: {self.total_active}\n"
            f"By workstream:\n{ws_lines or '  (none)'}"
            f"{om_line}"
        )

    def direct_answer(self) -> str:
        ws_label = (
            WORKSTREAM_LABELS.get(self.workstream, self.workstream)
            if self.workstream
            else None
        )
        scope = f"{ws_label} workstream'i için " if ws_label else "platform genelinde "
        breakdown = ", ".join(
            f"{WORKSTREAM_LABELS.get(ws, ws)}: {n}"
            for ws, n in sorted(self.by_workstream.items())
        )
        lines = [
            f"{scope}**Question Bank** data product port'u üzerinden **{self.total_active}** aktif soru tanımlı.",
            f"Kaynak: `{self.port}` (raw tablo değil).",
        ]
        if breakdown:
            lines.append(f"Workstream dağılımı: {breakdown}.")
        if self.om_contract_note:
            lines.append(f"Catalog (OpenMetadata): {self.om_contract_note}")
        return " ".join(lines)


def detect_question_bank_count_intent(message: str) -> bool:
    msg = message.lower()
    if not any(t in msg for t in QUESTION_COUNT_TRIGGERS):
        return False
    # Avoid matching "assessment" count style confusion when only assessment mentioned
    if "assessment" in msg and "soru" not in msg and "question" not in msg:
        return False
    return True


def extract_workstream_hint(message: str, session_workstream: str) -> str | None:
    msg = message.lower()
    for ws in WORKSTREAM_LABELS:
        if ws in msg or WORKSTREAM_LABELS[ws].lower() in msg:
            return ws
    if session_workstream and session_workstream not in ("general", ""):
        return session_workstream
    return None


def _find_product(product_id: str) -> dict | None:
    catalog = load_data_products_catalog()
    for product in catalog.get("published_data_products", []):
        if product.get("id") == product_id:
            return product
    return None


def _contract_summary(product: dict) -> str:
    tier = product.get("maturity_tier", "L0_listed")
    desc = (product.get("description") or "").strip().replace("\n", " ")
    if len(desc) > 200:
        desc = desc[:197] + "..."
    return f"tier={tier}; {desc}"


async def _om_product_note(product_name: str) -> str | None:
    try:
        from app.services.openmetadata_client import fetch_data_product_summary

        return await fetch_data_product_summary(product_name)
    except Exception:
        return None


async def _invoke_question_bank_port(
    db: AsyncSession,
    workstream: str | None,
) -> tuple[list[str], dict[str, int], int]:
    """Read via Question Bank port semantics (active questions only)."""
    q = (
        select(WorkstreamQuestion.workstream, func.count())
        .where(WorkstreamQuestion.is_active == True)  # noqa: E712
        .group_by(WorkstreamQuestion.workstream)
        .order_by(WorkstreamQuestion.workstream)
    )
    if workstream:
        q = (
            select(WorkstreamQuestion.workstream, func.count())
            .where(WorkstreamQuestion.is_active == True)  # noqa: E712
            .where(WorkstreamQuestion.workstream == workstream)
            .group_by(WorkstreamQuestion.workstream)
        )
    result = await db.execute(q)
    rows = result.all()
    by_ws = {row[0]: int(row[1]) for row in rows}
    total = sum(by_ws.values())
    port = (
        f"GET /api/v1/question-bank?workstream={workstream}"
        if workstream
        else "GET /api/v1/question-bank"
    )
    return [port], by_ws, total


async def try_route_product_query(
    db: AsyncSession,
    user_message: str,
    session_workstream: str,
    ontology_context: str = "",
) -> ProductRouteResult | None:
    """Resolve a user message to a data product port (prototype: question count)."""
    if not detect_question_bank_count_intent(user_message):
        return None

    steps: list[str] = []
    if ontology_context.strip():
        steps.append("KG/ontology context loaded for workstream semantics")
    elif any(h in user_message.lower() for h in QUESTION_ONTOLOGY_HINTS):
        steps.append("Keyword match: Question / Question Bank concepts")

    product = _find_product(QUESTION_BANK_PRODUCT_ID)
    if not product:
        return None

    steps.append(
        f"Catalog resolved product '{product.get('name')}' "
        f"(domain object: workstream_question)"
    )

    workstream = extract_workstream_hint(user_message, session_workstream)
    if workstream:
        steps.append(f"Workstream scope: {workstream}")
    else:
        steps.append("Workstream scope: all (global Question Bank)")

    ports, by_ws, total = await _invoke_question_bank_port(db, workstream)
    port = ports[0]
    steps.append(f"Invoked primary port: {port}")

    om_note = await _om_product_note(product.get("name", "Question Bank"))
    if om_note:
        steps.append("OpenMetadata product documentation merged into contract")

    return ProductRouteResult(
        intent="question_bank_count",
        product_id=QUESTION_BANK_PRODUCT_ID,
        product_name=product.get("name", "Question Bank"),
        workstream=workstream,
        port=port,
        contract_summary=_contract_summary(product),
        om_contract_note=om_note,
        total_active=total,
        by_workstream=by_ws,
        reasoning_steps=steps,
    )
