from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import assessments, health, interviews, tasks
from app.routers.findings import evidence_router, finding_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(finding_router, prefix="/api/v1")
