"""Posts review findings to a real GitHub PR via the `gh` CLI.

This is the one real side-effecting action in this feature — everything
upstream (retrieval, review, the severity cap) only decides *what* to
say; this module is the only place that actually writes to GitHub. Only
called when the CLI is given both --repo and --pr, and never for an empty
finding list (no noise on a clean PR).
"""

import subprocess

from .schemas import ReviewFinding

HEADER = "### \U0001f916 Automated review (review memory)"
FOOTER = (
    "_This is an automated first pass — a human review is still required before merge._"
)


def format_comment(findings: list[ReviewFinding]) -> str:
    """One consolidated markdown comment body for all findings."""
    lines = [HEADER, ""]
    for finding in findings:
        grounded = (
            f" _(grounded in past review `{finding.grounded_in}`)_"
            if finding.grounded_in
            else ""
        )
        lines.append(
            f"- **[{finding.severity}] {finding.category}** — `{finding.location}`{grounded}\n"
            f"  {finding.comment}"
        )
    lines.extend(["", FOOTER])
    return "\n".join(lines)


def post_comment(repo: str, pr_number: int, body: str) -> None:
    """Posts `body` as a single PR comment via the `gh` CLI.

    Requires GH_TOKEN/GITHUB_TOKEN in the environment — GitHub Actions'
    default token has this already; `gh` reads it without extra wiring.
    Raises on failure rather than swallowing it: a silently-failed post
    would look identical to "reviewed, found nothing," which is worse
    than a loud CI failure.
    """
    subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body],
        check=True,
    )
