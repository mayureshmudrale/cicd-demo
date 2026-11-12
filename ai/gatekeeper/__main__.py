"""CI entrypoint:

    python -m ai.gatekeeper [--tfplan plan.json] [--sql a.sql b.sql] \\
        [--openapi-before before.json --openapi-after after.json]

Runs whichever deterministic analyzers have inputs provided (all are
optional — a PR touching only app code with no migrations runs none of
them and passes trivially), combines their findings, and prints the
GatekeeperReport as JSON. Exits 1 when the verdict is "requires_approval"
so it can act as a real CI gate; in a non-POC setup this would more likely
map to a required-reviewer GitHub status than a hard failure.
"""

import argparse
import json

from .api_contract import analyze as analyze_api_contract
from .gate import gate
from .migration_risk import analyze as analyze_migration
from .schemas import Finding
from .terraform_risk import analyze as analyze_terraform


def _collect_findings(args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []

    if args.tfplan:
        with open(args.tfplan) as handle:
            findings.extend(analyze_terraform(json.load(handle)))

    for sql_path in args.sql or []:
        with open(sql_path) as handle:
            findings.extend(analyze_migration(handle.read(), location=sql_path))

    if args.openapi_before and args.openapi_after:
        with open(args.openapi_before) as handle:
            before = json.load(handle)
        with open(args.openapi_after) as handle:
            after = json.load(handle)
        findings.extend(analyze_api_contract(before, after))

    return findings


def main() -> None:
    """Parses CLI args, runs the applicable analyzers, prints the report."""
    parser = argparse.ArgumentParser(
        description="Pre-deployment blast radius gatekeeper"
    )
    parser.add_argument("--tfplan", help="path to `terraform show -json` output")
    parser.add_argument(
        "--sql", nargs="*", help="migration SQL file(s) changed in this PR"
    )
    parser.add_argument(
        "--openapi-before", help="OpenAPI JSON before this PR's changes"
    )
    parser.add_argument("--openapi-after", help="OpenAPI JSON after this PR's changes")
    args = parser.parse_args()

    report = gate(_collect_findings(args))
    print(report.model_dump_json(indent=2))
    raise SystemExit(1 if report.verdict == "requires_approval" else 0)


if __name__ == "__main__":
    main()
