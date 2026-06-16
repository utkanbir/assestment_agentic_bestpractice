# S6-BA-006: OpenTelemetry SDK — FastAPI distributed tracing
import os

from fastapi import FastAPI


def setup_tracing(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing with OTLP export to Tempo via OTel Collector."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        otel_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://aakp-otel-collector.aakp-monitoring.svc.cluster.local:4317",
        )

        resource = Resource.create({
            "service.name": "aakp-api",
            "service.namespace": "aakp",
            "deployment.environment": os.getenv("ENV", "production"),
        })

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(enable_commenter=True)
        HTTPXClientInstrumentor().instrument()

    except ImportError:
        import logging
        logging.getLogger("tracing").warning(
            "OpenTelemetry packages not installed — tracing disabled"
        )
