# S6-AA-001/002/003: LangFuse tracing for all agents
# - Wraps every LLM call with a LangFuse trace
# - Records token usage and cost per agent (S6-AA-002)
# - Sends confidence score as a score event (S6-AA-003)
import logging
import os

log = logging.getLogger("langfuse_tracer")

_LANGFUSE_HOST = os.getenv(
    "LANGFUSE_HOST",
    "http://aakp-langfuse.aakp-monitoring.svc.cluster.local:3000",
)
_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")


def _get_client():
    """Return LangFuse client, or None if not configured."""
    if not (_PUBLIC_KEY and _SECRET_KEY):
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=_PUBLIC_KEY,
            secret_key=_SECRET_KEY,
            host=_LANGFUSE_HOST,
        )
    except ImportError:
        log.warning("langfuse package not installed — tracing disabled")
        return None


def create_trace(name: str, agent: str, assessment_id: str | None = None):
    """Start a LangFuse trace for a single agent run."""
    client = _get_client()
    if client is None:
        return None
    meta = {"agent": agent}
    if assessment_id:
        meta["assessment_id"] = assessment_id
    return client.trace(name=name, metadata=meta, tags=[agent])


def record_llm_generation(
    trace,
    name: str,
    model: str,
    input_messages: list,
    output: str,
    usage: dict | None = None,
):
    """S6-AA-001/002: Record an LLM generation with token usage."""
    if trace is None:
        return None
    gen = trace.generation(
        name=name,
        model=model,
        input=input_messages,
        output=output,
        usage=usage or {},  # {"input": N, "output": M, "total": N+M}
    )
    # S6-AA-002: Prometheus token counters (imported lazily to avoid circular)
    try:
        from app.core.metrics import llm_calls_total, llm_tokens_total
        agent_label = trace.metadata.get("agent", "unknown") if hasattr(trace, "metadata") else "unknown"
        llm_calls_total.labels(agent=agent_label, model=model).inc()
        if usage:
            llm_tokens_total.labels(agent=agent_label, model=model, direction="input").inc(usage.get("input", 0))
            llm_tokens_total.labels(agent=agent_label, model=model, direction="output").inc(usage.get("output", 0))
    except Exception:
        pass
    return gen


def record_confidence_score(trace, score: float, comment: str = ""):
    """S6-AA-003: Send agent confidence score as a LangFuse score event."""
    if trace is None:
        return
    try:
        trace.score(name="confidence", value=score, comment=comment)
    except Exception as exc:
        log.debug("LangFuse score failed (non-fatal): %s", exc)


def flush():
    """Flush pending events to LangFuse — call at agent shutdown."""
    client = _get_client()
    if client:
        try:
            client.flush()
        except Exception:
            pass
