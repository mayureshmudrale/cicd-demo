"""Opens the verified, committed fix as a draft PR via the `gh` CLI —
the one real side-effecting action beyond the local branch commit
itself. Never merges anything; a human still has to review and merge the
draft, same as ai/reviewmem's posting step.
"""

import subprocess


def open_draft_pr(repo: str, branch: str, base: str, title: str, body: str) -> None:
    """Opens `branch` as a draft PR against `base`. Raises on failure
    rather than swallowing it — a silently-failed open would look
    identical to "nothing to report."""
    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--head",
            branch,
            "--base",
            base,
            "--draft",
            "--title",
            title,
            "--body",
            body,
        ],
        check=True,
    )
