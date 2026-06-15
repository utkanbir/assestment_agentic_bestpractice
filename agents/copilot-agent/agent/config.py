from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-8"
    api_base_url: str = "http://aakp-api.aakp-information.svc.cluster.local:8000"
    fuseki_url: str = "http://aakp-fuseki.aakp-information.svc.cluster.local:3030"

    class Config:
        env_file = ".env"


settings = Settings()
