from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Commute.ai - AI Agents"
    PROJECT_DESCRIPTION: str = "AI-powered route analysis and recommendations"
    VERSION: str = "0.6.0"
    API_V1_STR: str = "/api/v1"

    # LLM Configuration
    LLM_PROVIDER: str = "groq"

    # Groq Configuration
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # OpenAI Configuration (fallback)
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    class ConfigDict:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
