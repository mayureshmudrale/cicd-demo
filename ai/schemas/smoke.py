from pydantic import BaseModel


class SmokeTestResponse(BaseModel):
    ok: bool
    note: str
