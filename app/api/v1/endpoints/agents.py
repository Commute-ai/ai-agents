from fastapi import APIRouter

from app.agents import enhance

router = APIRouter()

@router.post("/enhance")
async def enhance_routes(body: enhance.InputSchema):
    return enhance.Agent.execute(body)
