from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AAKP API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://aakp:aakp-pg-secret@aakp-postgresql.aakp-information.svc.cluster.local:5432/aakp"

    redis_url: str = "redis://:aakp-redis-secret@aakp-redis.aakp-agent.svc.cluster.local:6379/0"
    kafka_bootstrap: str = "aakp-kafka.aakp-data.svc.cluster.local:9092"
    fuseki_url: str = "http://aakp-fuseki.aakp-knowledge.svc.cluster.local:3030"
    fuseki_public_url: str = "http://127.0.0.1:3030"
    fuseki_dataset: str = "aakp"
    qdrant_url: str = "http://aakp-qdrant.aakp-information.svc.cluster.local:6333"
    openmetadata_url: str = "http://aakp-openmetadata.aakp-information.svc.cluster.local:8585"
    audit_log_url: str = "http://aakp-audit-log.aakp-information.svc.cluster.local:8001"
    keycloak_url: str = "http://aakp-keycloak.aakp-agent.svc.cluster.local:8080"
    keycloak_realm: str = "aakp"
    opa_url: str = "http://aakp-opa.aakp-agent.svc.cluster.local:8181"
    presidio_analyzer_url: str = "http://aakp-presidio-analyzer.aakp-agent.svc.cluster.local:5001"
    presidio_anonymizer_url: str = "http://aakp-presidio-anonymizer.aakp-agent.svc.cluster.local:5002"
    # S6-DA: Observability service URLs
    otel_exporter_endpoint: str = "http://aakp-otel-collector.aakp-monitoring.svc.cluster.local:4317"
    langfuse_host: str = "http://aakp-langfuse.aakp-monitoring.svc.cluster.local:3000"


settings = Settings()
