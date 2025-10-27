from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Commute.ai - AI Agents"
    PROJECT_DESCRIPTION: str = "AI-powered route analysis and recommendations"
    VERSION: str = "0.4.0"
    API_V1_STR: str = "/api/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    AGENTS_PATH: str = "app/agents"

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
