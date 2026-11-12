from typing import Literal

from pydantic import BaseModel


class ReviewFinding(BaseModel):
    """One concrete review comment, ready to post."""

    location: str
    severity: Literal["low", "medium", "high"]
    category: str
    comment: str
    grounded_in: str | None = (
        None  # golden comment id, if this matches historical precedent
    )


class _GeminiFinding(BaseModel):
    """Gemini's own view of one finding, before `location` is attached."""

    severity: Literal["low", "medium", "high"]
    category: str
    comment: str
    grounded_in: str | None = None


class _ReviewResponse(BaseModel):
    findings: list[_GeminiFinding]
