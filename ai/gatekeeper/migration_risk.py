"""Deterministic static analysis of a raw SQL migration for unsafe DDL
patterns — regex-based, no AI involved. Catches the classic Postgres
footguns: a NOT NULL column added without a default (blocks writes on
every existing row while it backfills), a non-concurrent index build
(takes a table-wide lock), and a foreign key with no supporting index.
"""

import re

from .schemas import Finding

_ADD_NOT_NULL_NO_DEFAULT = re.compile(
    r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+\w+[\w()]*\s+NOT\s+NULL(?!.*\bDEFAULT\b)",
    re.IGNORECASE,
)
_CREATE_INDEX_NOT_CONCURRENT = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY\b)(\w+)",
    re.IGNORECASE,
)
_FOREIGN_KEY_COLUMN = re.compile(
    r"(\w+)\s+\w+[\w()]*\s+REFERENCES\s+(\w+)",
    re.IGNORECASE,
)


def analyze(sql: str, *, location: str = "migration.sql") -> list[Finding]:
    """`sql` is the raw contents of one migration file."""
    findings = []

    for match in _ADD_NOT_NULL_NO_DEFAULT.finditer(sql):
        findings.append(
            Finding(
                source="migration",
                location=f"{location}: column {match.group(1)!r}",
                severity="high",
                reason=(
                    "NOT NULL column added with no DEFAULT — every existing row must be "
                    "rewritten under an exclusive lock; split into add-nullable, backfill, "
                    "then add the constraint"
                ),
            )
        )

    for match in _CREATE_INDEX_NOT_CONCURRENT.finditer(sql):
        findings.append(
            Finding(
                source="migration",
                location=f"{location}: index {match.group(1)!r}",
                severity="medium",
                reason="CREATE INDEX without CONCURRENTLY holds a table-wide write lock",
            )
        )

    for match in _FOREIGN_KEY_COLUMN.finditer(sql):
        column, _referenced_table = match.groups()
        if not re.search(rf"\bINDEX\b[^;]*\({column}\)", sql, re.IGNORECASE):
            findings.append(
                Finding(
                    source="migration",
                    location=f"{location}: column {column!r}",
                    severity="low",
                    reason="foreign key column has no supporting index — joins and cascades will scan",
                )
            )

    return findings
