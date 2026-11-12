"""Deterministic IaC contract-drift check (ARCHITECTURE.md's own
`iac-contract.yml`): confirms every backend (aws/gcp/local) of each
module (network/cluster/database) declares the SAME contract variables
and outputs — catching the exact kind of drift that would otherwise only
surface as a runtime error in a cloud this repo has never actually
applied against.

Backend-specific extras (e.g. cluster/aws's kubernetes_version) are not
flagged — only the names ARCHITECTURE.md's own contract table lists.
"""
import re
import sys
from pathlib import Path

MODULES_DIR = Path(__file__).parent / "modules"
BACKENDS = ["aws", "gcp", "local"]

CONTRACT = {
    "network": {
        "variable": {"name", "region", "cidr"},
        "output": {"network_id", "private_subnet_ids"},
    },
    "cluster": {
        "variable": {"name", "tier", "network_id", "private_subnet_ids"},
        "output": {
            "cluster_name",
            "kube_host",
            "kube_ca",
            "kube_token",
            "ingress_annotations",
            "storage_class",
        },
    },
    "database": {
        "variable": {"name", "tier", "network_id", "allowed_from"},
        "output": {"database_url", "host", "port"},
    },
}

_BLOCK_NAME = re.compile(r'^\s*(variable|output)\s+"([^"]+)"\s*\{', re.MULTILINE)


def _declared_names(path: Path, kind: str) -> set[str]:
    """Every `variable "x" {` or `output "x" {` name in `path`, if it exists."""
    if not path.exists():
        return set()
    return {name for block_kind, name in _BLOCK_NAME.findall(path.read_text()) if block_kind == kind}


def check_module(module_name: str) -> list[str]:
    """Returns one error string per (backend, kind) missing a required contract name."""
    errors = []
    contract = CONTRACT[module_name]
    filenames = {"variable": "variables.tf", "output": "outputs.tf"}

    for kind, required in contract.items():
        for backend in BACKENDS:
            path = MODULES_DIR / module_name / backend / filenames[kind]
            missing = required - _declared_names(path, kind)
            if missing:
                errors.append(f"{module_name}/{backend}/{filenames[kind]}: missing {kind}(s) {sorted(missing)}")
    return errors


def main() -> int:
    """Runs `check_module` for every module in CONTRACT; prints and returns 1 on any drift, else 0."""
    all_errors = [error for module_name in CONTRACT for error in check_module(module_name)]

    if all_errors:
        print("IaC contract drift detected:")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print("IaC contract check passed: network/cluster/database all match across aws/gcp/local.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
