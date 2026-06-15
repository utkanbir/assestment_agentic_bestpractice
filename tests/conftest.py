"""
Test configuration.

Targets:
  API_BASE  — FastAPI (default: http://localhost:30080/api/v1)
  FUSEKI    — Apache Jena Fuseki (default: http://localhost:3030)
  PG_DSN    — PostgreSQL (default: local port-forward)

Override via env vars before running:
  $env:API_BASE = "http://localhost:8000/api/v1"
"""
import os
import pytest

API_BASE   = os.getenv("API_BASE",   "http://localhost:30080/api/v1")
FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
FUSEKI_DS  = os.getenv("FUSEKI_DS",  "aakp")
PG_DSN     = os.getenv("PG_DSN",     "postgresql://aakp:aakp-pg-secret@localhost:5433/aakp")
WS_BASE    = os.getenv("WS_BASE",    "ws://localhost:30080/ws")


@pytest.fixture(scope="session")
def api_base():
    return API_BASE


@pytest.fixture(scope="session")
def fuseki_url():
    return FUSEKI_URL


@pytest.fixture(scope="session")
def fuseki_ds():
    return FUSEKI_DS


@pytest.fixture(scope="session")
def ws_base():
    return WS_BASE
