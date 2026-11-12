from typing import Literal

from pydantic import BaseModel

Severity = Literal["low", "medium", "high", "critical"]


class Finding(BaseModel):
    """One concrete, deterministically-detected risk — never an AI guess."""

    source: Literal["terraform", "migration", "api_contract"]
    location: str
    severity: Severity
    reason: str


class GatekeeperReport(BaseModel):
    verdict: Literal["pass", "requires_approval"]
    findings: list[Finding]
    summary: str
    remediation_plan: str | None = None
