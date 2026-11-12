"""Splits a unified diff into (location, hunk_body) pairs — deterministic
text parsing, no AI involved."""

import re

_HUNK_HEADER = re.compile(r"^@@ .+ @@")
_FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")


def split_into_hunks(diff_text: str) -> list[tuple[str, str]]:
    """Returns one (location, hunk_body) pair per `@@ ... @@` hunk.

    Each hunk is tagged with whatever file was active when ITS header was
    seen (`header_file`) — not `current_file` at flush time, which by then
    may already have advanced to the next file's own `+++ b/` line.
    """
    hunks = []
    current_file = "unknown"
    header = None
    header_file = None
    lines: list[str] = []

    for line in diff_text.splitlines():
        file_match = _FILE_HEADER.match(line)
        if file_match:
            current_file = file_match.group(1)
            continue
        if _HUNK_HEADER.match(line):
            if header is not None:
                hunks.append((f"{header_file} {header}", "\n".join(lines)))
            header = line
            header_file = current_file
            lines = []
            continue
        if header is not None:
            lines.append(line)

    if header is not None:
        hunks.append((f"{header_file} {header}", "\n".join(lines)))
    return hunks
