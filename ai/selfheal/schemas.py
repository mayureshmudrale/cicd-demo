from pydantic import BaseModel


class FileEdit(BaseModel):
    path: str
    new_content: str


class PatchProposal(BaseModel):
    """Gemini's proposed fix — never trusted until apply.py verifies it
    for real against the original failing command and a safety net."""

    explanation: str
    edits: list[FileEdit]


class HealResult(BaseModel):
    """The outcome of actually trying a proposal in an isolated worktree."""

    fixed: bool
    safety_passed: bool
    explanation: str
    edits: list[FileEdit]

    @property
    def healed(self) -> bool:
        """True only if the original command now passes AND the safety
        net (if any was given) still passes too."""
        return self.fixed and self.safety_passed
