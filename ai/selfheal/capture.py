"""Deterministic evidence extraction from a failing command's output —
no AI involved. Finds the files a linter or a Python traceback points at,
and reads their current content; never reads a file the output didn't
actually name, and never reads outside the repo even if the output
somehow pointed there.
"""

import re
from pathlib import Path

_TRACEBACK_FILE = re.compile(r'File "([^"]+)", line \d+')
# Grep-style linter output (ruff --output-format=concise, flake8, ...):
_LINTER_FILE_CONCISE = re.compile(r"^([^\s:]+\.py):\d+:", re.MULTILINE)
# ruff's current default "full" format points at the file with "--> path:line:col":
_LINTER_FILE_ARROW = re.compile(r"^\s*-->\s+(\S+\.py):\d+:\d+", re.MULTILINE)


def _resolve_within_repo(
    candidate: str, *, repo_root: Path, search_root: Path
) -> Path | None:
    """None if `candidate` doesn't resolve to a real file inside repo_root."""
    path = (search_root / candidate).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        return None  # outside the repo; never read it
    return path if path.is_file() else None


def extract_implicated_files(
    output: str, *, repo_root: Path, search_root: Path
) -> dict[str, str]:
    """Returns {path relative to repo_root: current content} for every
    file the command's output names that actually exists in the repo."""
    repo_root = repo_root.resolve()
    candidates = (
        set(_TRACEBACK_FILE.findall(output))
        | set(_LINTER_FILE_CONCISE.findall(output))
        | set(_LINTER_FILE_ARROW.findall(output))
    )

    files = {}
    for candidate in candidates:
        resolved = _resolve_within_repo(
            candidate, repo_root=repo_root, search_root=search_root
        )
        if resolved is not None:
            files[str(resolved.relative_to(repo_root))] = resolved.read_text()
    return files
