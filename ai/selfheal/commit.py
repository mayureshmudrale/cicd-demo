"""Commits a verified HealResult to a new branch — via a disposable
worktree, same as apply.py, so this never touches whatever the caller
currently has checked out or any uncommitted changes there. The branch
itself does persist in the repo after the worktree is removed (a
worktree is just a checkout of a branch, not the branch itself); opening
it as a draft PR is a separate, explicit step in post.py.
"""

import subprocess
import tempfile
from pathlib import Path

from .schemas import HealResult


def commit_to_branch(repo_root: Path, branch: str, result: HealResult) -> None:
    """Creates `branch` off HEAD and commits `result`'s edits to it."""
    with tempfile.TemporaryDirectory() as tmp:
        worktree = Path(tmp) / "heal-branch"
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(worktree), "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        try:
            for edit in result.edits:
                (worktree / edit.path).write_text(edit.new_content)
            subprocess.run(["git", "add", "."], cwd=worktree, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"self-heal: {result.explanation}"],
                cwd=worktree,
                check=True,
            )
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=repo_root,
                check=False,
            )
