from pydantic import BaseModel

from app.agents.base import BaseAgent


class AnnotationResultStop(BaseModel):
    location: str
    arrival_time: str
    departure_time: str
    landmarks: list[str]


class AnnotationRouteOption(BaseModel):
    description: str
    summary: str
    stops: list[AnnotationResultStop]


class OutputSchema(BaseModel):
    options: list[AnnotationRouteOption]


class InputSchema(BaseModel):
    start_location: str
    end_location: str


class Agent(BaseAgent[InputSchema, OutputSchema]):
    pass
