"""Applies a PatchProposal in a disposable git worktree and re-runs BOTH
the original failing command and a broader safety-net command for real,
before ever reporting success. This is the actual gate: a proposal is
never trusted on Gemini's word alone, and this never mutates the caller's
real working tree or current branch — only a temporary worktree that's
removed before returning either way.
"""

import subprocess
import tempfile
from pathlib import Path

from .schemas import HealResult, PatchProposal


def _run(command: list[str], cwd: Path) -> bool:
    return (
        subprocess.run(command, cwd=cwd, capture_output=True, text=True).returncode == 0
    )


def apply_and_verify(
    repo_root: Path,
    proposal: PatchProposal,
    *,
    fix_command: list[str],
    safety_command: list[str] | None,
    cwd_relative: str,
) -> HealResult:
    """Applies `proposal` on top of HEAD in a fresh worktree, re-runs
    `fix_command` (must now succeed) and `safety_command` (must still
    succeed, if given), and reports whether it's genuinely fixed.
    """
    with tempfile.TemporaryDirectory() as tmp:
        worktree = Path(tmp) / "verify"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        try:
            for edit in proposal.edits:
                (worktree / edit.path).write_text(edit.new_content)

            fixed = _run(fix_command, worktree / cwd_relative)
            safety_passed = (
                _run(safety_command, worktree / cwd_relative)
                if safety_command
                else True
            )

            return HealResult(
                fixed=fixed,
                safety_passed=safety_passed,
                explanation=proposal.explanation,
                edits=proposal.edits if (fixed and safety_passed) else [],
            )
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=repo_root,
                check=False,
            )
