import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.config import settings
from app.utils import logger as _  # noqa: F401 - Import to configure logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
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
