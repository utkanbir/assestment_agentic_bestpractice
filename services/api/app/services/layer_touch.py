"""
Layer touch instrumentation — records which architecture layer/technology each operation uses.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import LayerTransaction
from app.models.layer_touch import LayerTouchEvent
from app.schemas.architecture import (
    LayerTouchOut,
    LayerTouchSummaryOut,
    LayerTransactionDetailOut,
    LayerTransactionOut,
)

logger = logging.getLogger(__name__)

_operation_ctx: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "layer_touch_operation", default=None
)
_trace_results: contextvars.ContextVar[list[LayerTouchOut] | None] = contextvars.ContextVar(
    "layer_touch_trace", default=None
)


def begin_operation(
    operation: str,
    *,
    source: str = "api",
    interview_id: uuid.UUID | None = None,
    assessment_id: uuid.UUID | None = None,
    chat_session_id: uuid.UUID | None = None,
    summary: str | None = None,
) -> None:
    tx_id = uuid.uuid4()
    _operation_ctx.set({
        "operation": operation,
        "source": source,
        "interview_id": interview_id,
        "assessment_id": assessment_id,
        "chat_session_id": chat_session_id,
        "transaction_id": tx_id,
        "step_order": 0,
        "summary": summary,
        "started_at_monotonic": time.perf_counter(),
    })
    _trace_results.set([])


def clear_operation() -> None:
    _operation_ctx.set(None)
    _trace_results.set(None)


def get_trace() -> list[LayerTouchOut]:
    trace = _trace_results.get()
    return list(trace) if trace else []


def get_transaction_id() -> uuid.UUID | None:
    ctx = _operation_ctx.get() or {}
    tx_id = ctx.get("transaction_id")
    if isinstance(tx_id, uuid.UUID):
        return tx_id
    if isinstance(tx_id, str):
        try:
            return uuid.UUID(tx_id)
        except ValueError:
            return None
    return None


async def record_touch(
    db: AsyncSession | None,
    layer: str,
    technology: str,
    action: str,
    *,
    operation: str | None = None,
    interview_id: uuid.UUID | None = None,
    assessment_id: uuid.UUID | None = None,
    detail: dict | None = None,
    duration_ms: int | None = None,
    broadcast: bool = True,
) -> LayerTouchOut | None:
    ctx = _operation_ctx.get() or {}
    op = operation or ctx.get("operation") or "unknown"
    iid = interview_id if interview_id is not None else ctx.get("interview_id")
    aid = assessment_id if assessment_id is not None else ctx.get("assessment_id")
    tx_id = ctx.get("transaction_id")
    if tx_id and isinstance(tx_id, str):
        tx_id = uuid.UUID(tx_id)

    if db is None:
        return None

    if tx_id:
        await _ensure_transaction(
            db,
            transaction_id=tx_id,
            operation=op,
            source=ctx.get("source", "api"),
            assessment_id=aid,
            interview_id=iid,
            chat_session_id=ctx.get("chat_session_id"),
            summary=ctx.get("summary"),
            metadata_json=ctx.get("metadata_json"),
        )

    next_step = int(ctx.get("step_order", 0)) + 1
    ctx["step_order"] = next_step
    _operation_ctx.set(ctx)

    event = LayerTouchEvent(
        operation=op,
        interview_id=iid,
        assessment_id=aid,
        transaction_id=tx_id,
        step_order=next_step if tx_id else None,
        layer=layer,
        technology=technology,
        action=action,
        detail=detail,
        duration_ms=duration_ms,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    out = LayerTouchOut.model_validate(event)

    trace = _trace_results.get()
    if trace is not None:
        trace.append(out)

    if tx_id:
        await _refresh_transaction_metrics(db, tx_id, ctx)

    if broadcast and iid:
        await _broadcast_layer_touch(str(iid), out)

    return out


@asynccontextmanager
async def touch(
    db: AsyncSession,
    layer: str,
    technology: str,
    action: str,
    detail: dict | None = None,
):
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        await record_touch(
            db, layer, technology, action, detail=detail, duration_ms=duration_ms
        )


def finish_operation() -> list[LayerTouchOut]:
    trace = get_trace()
    clear_operation()
    return trace


async def list_touches(
    db: AsyncSession,
    *,
    assessment_id: uuid.UUID | None = None,
    interview_id: uuid.UUID | None = None,
    layer: str | None = None,
    limit: int = 100,
) -> list[LayerTouchOut]:
    q = select(LayerTouchEvent).order_by(LayerTouchEvent.created_at.desc()).limit(limit)
    if assessment_id:
        q = q.where(LayerTouchEvent.assessment_id == assessment_id)
    if interview_id:
        q = q.where(LayerTouchEvent.interview_id == interview_id)
    if layer:
        q = q.where(LayerTouchEvent.layer == layer)
    result = await db.execute(q)
    return [LayerTouchOut.model_validate(r) for r in result.scalars().all()]


async def touch_summary(
    db: AsyncSession,
    *,
    assessment_id: uuid.UUID | None = None,
    interview_id: uuid.UUID | None = None,
) -> list[LayerTouchSummaryOut]:
    q = select(
        LayerTouchEvent.layer,
        func.count(LayerTouchEvent.id).label("touch_count"),
        func.max(LayerTouchEvent.operation).label("last_operation"),
        func.max(LayerTouchEvent.created_at).label("last_at"),
    )
    if assessment_id:
        q = q.where(LayerTouchEvent.assessment_id == assessment_id)
    if interview_id:
        q = q.where(LayerTouchEvent.interview_id == interview_id)
    q = q.group_by(LayerTouchEvent.layer)

    result = await db.execute(q)
    return [
        LayerTouchSummaryOut(
            layer=row.layer,
            touch_count=row.touch_count,
            last_operation=row.last_operation,
            last_at=row.last_at,
        )
        for row in result.all()
    ]


async def _broadcast_layer_touch(interview_id: str, touch: LayerTouchOut) -> None:
    try:
        from app.routers.ws import WSEventType, WSMessage, manager
        await manager.broadcast(
            interview_id,
            WSMessage(
                event=WSEventType.LAYER_TOUCH,
                payload={"touch": touch.model_dump(mode="json")},
            ),
        )
    except Exception as exc:
        logger.debug("WS layer.touch broadcast skipped: %s", exc)


async def list_transactions(
    db: AsyncSession,
    *,
    assessment_id: uuid.UUID | None = None,
    source: str | None = None,
    limit: int = 100,
) -> list[LayerTransactionOut]:
    q = select(LayerTransaction).order_by(LayerTransaction.started_at.desc()).limit(limit)
    if assessment_id:
        q = q.where(LayerTransaction.assessment_id == assessment_id)
    if source:
        q = q.where(LayerTransaction.source == source)
    result = await db.execute(q)
    txs = result.scalars().all()
    return [LayerTransactionOut.model_validate(tx) for tx in txs]


async def get_transaction_detail(
    db: AsyncSession,
    transaction_id: uuid.UUID,
) -> LayerTransactionDetailOut | None:
    tx = await db.get(LayerTransaction, transaction_id)
    if not tx:
        return None

    events_result = await db.execute(
        select(LayerTouchEvent)
        .where(LayerTouchEvent.transaction_id == transaction_id)
        .order_by(
            LayerTouchEvent.step_order.asc().nulls_last(),
            LayerTouchEvent.created_at.asc(),
        )
    )
    steps = [LayerTouchOut.model_validate(ev) for ev in events_result.scalars().all()]
    return LayerTransactionDetailOut(
        **LayerTransactionOut.model_validate(tx).model_dump(),
        steps=steps,
    )


async def _ensure_transaction(
    db: AsyncSession,
    *,
    transaction_id: uuid.UUID,
    operation: str,
    source: str,
    assessment_id: uuid.UUID | None,
    interview_id: uuid.UUID | None,
    chat_session_id: uuid.UUID | None,
    summary: str | None,
    metadata_json: dict | None,
) -> LayerTransaction:
    tx = await db.get(LayerTransaction, transaction_id)
    if tx:
        return tx
    tx = LayerTransaction(
        id=transaction_id,
        operation=operation,
        source=source,
        assessment_id=assessment_id,
        interview_id=interview_id,
        chat_session_id=chat_session_id,
        summary=summary,
        metadata_json=metadata_json,
        status="in_progress",
    )
    db.add(tx)
    await db.flush()
    return tx


async def _refresh_transaction_metrics(
    db: AsyncSession,
    transaction_id: uuid.UUID,
    ctx: dict[str, Any],
) -> None:
    tx = await db.get(LayerTransaction, transaction_id)
    if not tx:
        return
    elapsed_ms = int((time.perf_counter() - float(ctx.get("started_at_monotonic", time.perf_counter()))) * 1000)
    tx.total_duration_ms = elapsed_ms
    tx.status = "completed"
    tx.ended_at = datetime.now(timezone.utc)
    await db.flush()
