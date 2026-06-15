from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = "http://aakp-api.aakp-information.svc.cluster.local:8000"
    kafka_bootstrap: str = "aakp-kafka.aakp-data.svc.cluster.local:9092"


settings = Settings()
