"""Deterministic risk analysis of a real `terraform show -json <plan>`
plan — no AI involved. Flags destructive actions (delete/replace) and
overly-broad access (public CIDRs, wildcard IAM/RBAC grants) by walking
the plan's own structured JSON, not by asking a model to guess.

STATEFUL_HINTS and the pattern scanner are heuristics, not an exhaustive
taxonomy — tuned for what this repo's own modules (Kubernetes, Cilium,
CloudNativePG) actually emit, not every possible Terraform provider.
"""

from .schemas import Finding

STATEFUL_HINTS = ("database", "cluster", "pg", "postgres", "sql", "volume", "pvc")
PUBLIC_CIDR = "0.0.0.0/0"
WILDCARD_KEY_HINTS = ("verb", "action", "resource", "permission")


def _destructive_severity(
    resource_type: str, address: str, actions: list[str]
) -> str | None:
    """None if this change isn't destructive; otherwise a severity.

    Checks both the Terraform resource `type` and its `address`: a CRD
    applied via a generic `kubectl_manifest`/`kubernetes_manifest` type
    (e.g. this repo's own CloudNativePG `Cluster`) never reveals what it
    actually manages through `type` alone — only its address does.
    """
    if "delete" not in actions:
        return None
    is_replace = "create" in actions
    haystack = f"{resource_type} {address}".lower()
    is_stateful = any(hint in haystack for hint in STATEFUL_HINTS)
    if is_stateful:
        return "high" if is_replace else "critical"
    return "medium" if is_replace else "high"


def _scan_for_broad_access(value, path: str) -> list[Finding]:
    """Recursively walks a plan value for public CIDRs and wildcard grants."""
    findings = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(_scan_for_broad_access(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_scan_for_broad_access(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        findings.extend(_string_findings(value, path))
    return findings


def _string_findings(value: str, path: str) -> list[Finding]:
    if PUBLIC_CIDR in value:
        return [
            Finding(
                source="terraform",
                location=path,
                severity="high",
                reason=f"{PUBLIC_CIDR} grants access from the entire public internet",
            )
        ]
    key = path.rsplit(".", 1)[-1].lower()
    if value == "*" and any(hint in key for hint in WILDCARD_KEY_HINTS):
        return [
            Finding(
                source="terraform",
                location=path,
                severity="high",
                reason="wildcard ('*') grants unrestricted access instead of a named scope",
            )
        ]
    return []


def analyze(plan: dict) -> list[Finding]:
    """`plan` is the parsed JSON from `terraform show -json <planfile>`."""
    findings = []
    for change in plan.get("resource_changes", []):
        address = change["address"]
        actions = change["change"]["actions"]

        severity = _destructive_severity(change["type"], address, actions)
        if severity:
            findings.append(
                Finding(
                    source="terraform",
                    location=address,
                    severity=severity,
                    reason=f"plan would {'/'.join(actions)} this resource",
                )
            )

        state = change["change"].get("after") or change["change"].get("before") or {}
        findings.extend(_scan_for_broad_access(state, address))
    return findings
