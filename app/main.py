from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.config import settings
from app.services.llm.utils import create_llm_from_config
from app.utils import logger as _  # noqa: F401 - Import to configure logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for initializing and cleaning up resources.
    """
    # Initialize singleton services
    logger.info("Initializing LLM provider...")

    # Skip real LLM provider initialization if dependency overrides are present (testing mode)
    if not app.dependency_overrides:
        app.state.llm_provider = create_llm_from_config()
        logger.info("LLM provider initialized successfully")
    else:
        logger.info("Skipping LLM provider initialization (test mode)")

    yield

    # Cleanup resources (if needed)
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Starting %s version v%s", settings.PROJECT_NAME, settings.VERSION)

app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": f"{settings.PROJECT_NAME} is running!",
        "version": settings.VERSION,
    }
