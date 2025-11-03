from pydantic import BaseModel


class Preference(BaseModel):
    prompt: str
