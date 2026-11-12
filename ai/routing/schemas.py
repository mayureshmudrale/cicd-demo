from typing import Literal

from pydantic import BaseModel


class RoutingDecision(BaseModel):
    action: Literal["advance", "hold", "rollback"]
    reasoning: str
