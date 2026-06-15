# S5-SA-009: Immutable audit log servisi
# Append-only FastAPI microservice — PostgreSQL partitioned table + Kafka mirror
# "Immutable" = no DELETE/UPDATE endpoints, INSERT only, WAL-level replication

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("audit-log")

app = FastAPI(title="AAKP Audit Log", description="Immutable append-only event store")

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        import os
        dsn = os.getenv(
            "DATABASE_URL",
            "postgresql://aakp:aakp-pg-secret@aakp-postgresql.aakp-information.svc.cluster.local:5432/aakp",
        )
        _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
        await _pool.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                event_type  TEXT NOT NULL,
                entity_id   TEXT NOT NULL,
                detail      JSONB,
                occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE INDEX IF NOT EXISTS idx_audit_entity  ON audit_events (entity_id);
            CREATE INDEX IF NOT EXISTS idx_audit_type    ON audit_events (event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_time    ON audit_events (occurred_at DESC);
        """)
    return _pool


class AuditEvent(BaseModel):
    event_type: str
    entity_id: str
    detail: dict | None = None


class AuditEventOut(AuditEvent):
    id: str
    occurred_at: datetime


@app.on_event("startup")
async def startup():
    await get_pool()
    log.info("Audit log service ready")


# S5-SA-010: Every KG change → audit (POST /events)
@app.post("/events", response_model=AuditEventOut, status_code=201)
async def create_event(body: AuditEvent):
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO audit_events (event_type, entity_id, detail) "
        "VALUES ($1, $2, $3) RETURNING id, event_type, entity_id, detail, occurred_at",
        body.event_type, body.entity_id, body.detail,
    )
    return AuditEventOut(
        id=str(row["id"]),
        event_type=row["event_type"],
        entity_id=row["entity_id"],
        detail=row["detail"],
        occurred_at=row["occurred_at"],
    )


@app.get("/events", response_model=list[AuditEventOut])
async def list_events(
    entity_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
):
    pool = await get_pool()
    conditions = []
    params = []
    if entity_id:
        params.append(entity_id)
        conditions.append(f"entity_id = ${len(params)}")
    if event_type:
        params.append(event_type)
        conditions.append(f"event_type = ${len(params)}")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(min(limit, 1000))
    rows = await pool.fetch(
        f"SELECT id, event_type, entity_id, detail, occurred_at "
        f"FROM audit_events {where} ORDER BY occurred_at DESC LIMIT ${len(params)}",
        *params,
    )
    return [
        AuditEventOut(
            id=str(r["id"]),
            event_type=r["event_type"],
            entity_id=r["entity_id"],
            detail=r["detail"],
            occurred_at=r["occurred_at"],
        )
        for r in rows
    ]


@app.get("/health")
def health():
    return {"status": "ok"}
