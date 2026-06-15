from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = "http://aakp-api.aakp-information.svc.cluster.local:8000"
    qdrant_url: str = "http://aakp-qdrant.aakp-information.svc.cluster.local:6333"

    kafka_bootstrap: str = "aakp-kafka.aakp-data.svc.cluster.local:9092"
    kafka_group_id: str = "memory-agent-group"


settings = Settings()
