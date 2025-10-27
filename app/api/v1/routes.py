from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    agents,
)

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
