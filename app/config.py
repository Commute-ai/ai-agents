from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Commute.ai - AI Agents"
    PROJECT_DESCRIPTION: str = "AI-powered route analysis and recommendations"
    VERSION: str = "0.7.0"
    API_V1_STR: str = "/api/v1"

    class ConfigDict:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
