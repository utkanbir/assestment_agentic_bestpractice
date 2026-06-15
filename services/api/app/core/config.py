from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AAKP API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://aakp:aakp-pg-secret@aakp-postgresql.aakp-information.svc.cluster.local:5432/aakp"

    redis_url: str = "redis://:aakp-redis-secret@aakp-redis.aakp-agent.svc.cluster.local:6379/0"
    kafka_bootstrap: str = "aakp-kafka.aakp-data.svc.cluster.local:9092"
    fuseki_url: str = "http://aakp-fuseki.aakp-knowledge.svc.cluster.local:3030"
    fuseki_dataset: str = "aakp"
    qdrant_url: str = "http://aakp-qdrant.aakp-information.svc.cluster.local:6333"


settings = Settings()
