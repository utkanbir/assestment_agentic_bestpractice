import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageExchangeOut,
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionOut,
    ChatSessionUpdate,
)
from app.services import layer_touch as layer_touch_svc
from app.services.chat_platform import build_platform_context, should_include_assessment_results
from app.services.llm_client import chat_assistant_reply
from app.services.product_router import try_route_product_query
from app.services.sparql_client import sparql_client

router = APIRouter(prefix="/chat", tags=["chat"])

GENERAL_WORKSTREAM = "general"
QDRANT_FALLBACK_WS = "kubernetes"


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def create_chat_session(body: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(
        assessment_id=body.assessment_id,
        workstream=body.workstream or GENERAL_WORKSTREAM,
        title=body.title or "Yeni Sohbet",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_chat_sessions(
    assessment_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(ChatSession).order_by(ChatSession.created_at.desc())
    if assessment_id:
        q = q.where(ChatSession.assessment_id == assessment_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_chat_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.patch("/sessions/{session_id}", response_model=ChatSessionOut)
async def update_chat_session(
    session_id: uuid.UUID,
    body: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def list_chat_messages(
    session_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    before: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    q = select(ChatMessage).where(ChatMessage.session_id == session_id)
    if before:
        before_msg = await db.get(ChatMessage, before)
        if before_msg:
            q = q.where(ChatMessage.created_at < before_msg.created_at)
    q = q.order_by(ChatMessage.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(reversed(result.scalars().all()))


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageExchangeOut)
async def add_chat_message(
    session_id: uuid.UUID,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    layer_touch_svc.begin_operation(
        "chat_message",
        source="chat",
        assessment_id=session.assessment_id,
        chat_session_id=session.id,
        summary="Genel chat etkileşimi",
    )

    user_msg = ChatMessage(session_id=session.id, role="user", content=body.content.strip())
    db.add(user_msg)
    await db.flush()
    await db.refresh(user_msg)
    await layer_touch_svc.record_touch(
        db,
        "information",
        "postgresql",
        "write",
        detail={"table": "chat_messages", "role": "user"},
    )

    hist_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id, ChatMessage.id != user_msg.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(12)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(hist_result.scalars().all())
    ]

    include_results = bool(
        session.assessment_id and should_include_assessment_results(body.content)
    )
    platform_context = await build_platform_context(
        db, session.assessment_id, include_results=include_results,
    )
    if include_results:
        await layer_touch_svc.record_touch(
            db,
            "information",
            "assessment_results_view",
            "read",
            detail={"product_id": "assessment_results_view", "assessment_id": str(session.assessment_id)},
        )


    qdrant_ws = (
        session.workstream
        if session.workstream and session.workstream != GENERAL_WORKSTREAM
        else QDRANT_FALLBACK_WS
    )
    doc_context = ""
    try:
        from app.services.qdrant_client import search_documents

        chunks = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: search_documents(body.content, qdrant_ws, limit=3),
        )
        doc_context = "\n".join(chunk["text"] for chunk in chunks)
        await layer_touch_svc.record_touch(
            db,
            "information",
            "qdrant",
            "search",
            detail={"chunks": len(chunks), "workstream": qdrant_ws},
        )
    except Exception:
        await layer_touch_svc.record_touch(
            db,
            "information",
            "qdrant",
            "search",
            detail={"chunks": 0, "workstream": qdrant_ws, "status": "unavailable"},
        )

    ontology_ws = qdrant_ws
    ontology_context = ""
    try:
        from app.services.agent_knowledge_context import build_kg_context
        ontology_context, kg_hits, _ = await build_kg_context(ontology_ws)
        await layer_touch_svc.record_touch(
            db,
            "knowledge",
            "fuseki",
            "read",
            detail={"operation": "chat_context", "workstream": ontology_ws, "hits": kg_hits},
        )
    except Exception:
        await layer_touch_svc.record_touch(
            db,
            "knowledge",
            "fuseki",
            "read",
            detail={"operation": "chat_context", "workstream": ontology_ws, "status": "unavailable"},
        )

    product_route = await try_route_product_query(
        db,
        body.content,
        session.workstream,
        ontology_context=ontology_context,
    )
    product_context = ""
    reply: str
    if product_route:
        product_context = product_route.format_for_llm()
        await layer_touch_svc.record_touch(
            db,
            "information",
            "data_products_catalog",
            "read",
            detail={"product_id": product_route.product_id, "intent": product_route.intent},
        )
        await layer_touch_svc.record_touch(
            db,
            "information",
            "question_bank",
            "read",
            detail={
                "port": product_route.port,
                "workstream": product_route.workstream,
                "total": product_route.total_active,
            },
        )
        if product_route.om_contract_note:
            await layer_touch_svc.record_touch(
                db,
                "information",
                "openmetadata",
                "read",
                detail={"product": product_route.product_name, "operation": "contract_discovery"},
            )
        reply = product_route.direct_answer()
    else:
        reply = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: chat_assistant_reply(
                workstream=session.workstream,
                user_message=body.content,
                doc_context=doc_context,
                ontology_context=ontology_context,
                history=history,
                platform_context=platform_context,
                product_context=product_context,
            ),
        )
        await layer_touch_svc.record_touch(
            db,
            "agent",
            "claude",
            "infer",
            detail={"operation": "chat_message", "workstream": session.workstream},
        )

    if product_route:
        await layer_touch_svc.record_touch(
            db,
            "agent",
            "product_router",
            "route",
            detail={
                "intent": product_route.intent,
                "product_id": product_route.product_id,
                "port": product_route.port,
            },
        )

    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=reply)
    db.add(assistant_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(assistant_msg)
    await layer_touch_svc.record_touch(
        db,
        "information",
        "postgresql",
        "write",
        detail={"table": "chat_messages", "role": "assistant"},
    )
    await db.commit()

    transaction_id = layer_touch_svc.get_transaction_id()
    trace = layer_touch_svc.finish_operation()
    return ChatMessageExchangeOut(
        session_id=session.id,
        user_message=ChatMessageOut.model_validate(user_msg),
        assistant_message=ChatMessageOut.model_validate(assistant_msg),
        layer_trace=trace,
        transaction_id=transaction_id,
    )
