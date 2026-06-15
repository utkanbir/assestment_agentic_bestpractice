from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    api_base_url: str = "http://aakp-api.aakp-information.svc.cluster.local:8000"
    fuseki_url: str = "http://aakp-fuseki.aakp-knowledge.svc.cluster.local:3030"
    fuseki_dataset: str = "aakp"
    fuseki_user: str = "admin"
    fuseki_password: str = "aakp-fuseki-secret"

    kafka_bootstrap: str = "aakp-kafka.aakp-data.svc.cluster.local:9092"
    kafka_group_id: str = "orchestrator-agent-group"

    postgres_url: str = "postgresql://aakp:aakp-pg-secret@aakp-postgresql.aakp-information.svc.cluster.local:5432/aakp"


settings = Settings()
