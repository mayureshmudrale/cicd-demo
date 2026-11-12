"""Deterministic diff of two OpenAPI schemas (before/after) for breaking
changes — no AI involved. Only the structural, unambiguous breaks: a
removed path/method, a removed field, or a field that became required
(existing callers who never set it would now fail validation).
"""

from .schemas import Finding


def _removed_routes(before: dict, after: dict) -> list[Finding]:
    findings = []
    before_paths = before.get("paths", {})
    after_paths = after.get("paths", {})
    for path, methods in before_paths.items():
        after_methods = after_paths.get(path, {})
        for method in methods:
            if method not in after_methods:
                findings.append(
                    Finding(
                        source="api_contract",
                        location=f"{method.upper()} {path}",
                        severity="high",
                        reason="endpoint removed or method no longer supported",
                    )
                )
    return findings


def _schema_field_changes(before: dict, after: dict) -> list[Finding]:
    findings = []
    before_schemas = before.get("components", {}).get("schemas", {})
    after_schemas = after.get("components", {}).get("schemas", {})
    for name, before_schema in before_schemas.items():
        after_schema = after_schemas.get(name)
        if after_schema is None:
            continue
        findings.extend(_removed_fields(name, before_schema, after_schema))
        findings.extend(_newly_required_fields(name, before_schema, after_schema))
    return findings


def _removed_fields(
    name: str, before_schema: dict, after_schema: dict
) -> list[Finding]:
    before_props = set(before_schema.get("properties", {}))
    after_props = set(after_schema.get("properties", {}))
    return [
        Finding(
            source="api_contract",
            location=f"{name}.{field}",
            severity="high",
            reason="field removed from the schema — existing consumers reading it will break",
        )
        for field in sorted(before_props - after_props)
    ]


def _newly_required_fields(
    name: str, before_schema: dict, after_schema: dict
) -> list[Finding]:
    newly_required = set(after_schema.get("required", [])) - set(
        before_schema.get("required", [])
    )
    return [
        Finding(
            source="api_contract",
            location=f"{name}.{field}",
            severity="medium",
            reason="field became required — existing callers who omit it will now fail validation",
        )
        for field in sorted(newly_required)
    ]


def analyze(before: dict, after: dict) -> list[Finding]:
    """`before`/`after` are two full OpenAPI documents (e.g. from `app.openapi()`)."""
    return _removed_routes(before, after) + _schema_field_changes(before, after)
