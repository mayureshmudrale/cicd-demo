"""CI entrypoint:

    python -m ai.selfheal --cmd "ruff check ." --cwd app/backend \\
        [--safety-cmd "pytest tests/"] [--branch heal/ci-123] \\
        [--repo owner/repo --base main]

Runs --cmd for real. If (and only if) it fails, captures evidence,
proposes a fix via Gemini, and verifies the fix in a disposable git
worktree (never the live working tree) before ever touching a real
branch. Commits to --branch only if the fix verifies; opens a draft PR
only if --branch and --repo are both given. Never merges anything.
"""

import argparse
import shlex
import subprocess
from pathlib import Path

from .apply import apply_and_verify
from .capture import extract_implicated_files
from .heal import propose_fix


def _run_and_capture(command: list[str], cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Self-healing CI: propose and verify a fix for a failing command"
    )
    parser.add_argument(
        "--cmd", required=True, help="the failing command, e.g. 'ruff check .'"
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="directory to run --cmd from, relative to --repo-root",
    )
    parser.add_argument(
        "--safety-cmd",
        help="broader command that must still pass, e.g. the full test suite",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--branch", help="branch to commit a verified fix to")
    parser.add_argument(
        "--repo", help="owner/repo to open a draft PR in, e.g. $GITHUB_REPOSITORY"
    )
    parser.add_argument("--base", default="main", help="base branch for the draft PR")
    return parser.parse_args()


def main() -> None:
    """Runs --cmd; on failure, proposes and verifies a fix, optionally committing and opening a draft PR."""
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    cwd = repo_root / args.cwd
    command = shlex.split(args.cmd)

    ok, output = _run_and_capture(command, cwd)
    if ok:
        print("self-heal: command already passes, nothing to heal.")
        return

    print(f"self-heal: '{args.cmd}' failed, attempting to propose a fix...")
    implicated = extract_implicated_files(output, repo_root=repo_root, search_root=cwd)
    if not implicated:
        print(
            "self-heal: could not identify any implicated file from the output; needs a human."
        )
        raise SystemExit(1)

    proposal = propose_fix(args.cmd, output, implicated)
    if proposal is None:
        print(
            "self-heal: Gemini unavailable, no safe fallback for patch generation; needs a human."
        )
        raise SystemExit(1)

    safety_command = shlex.split(args.safety_cmd) if args.safety_cmd else None
    result = apply_and_verify(
        repo_root,
        proposal,
        fix_command=command,
        safety_command=safety_command,
        cwd_relative=args.cwd,
    )

    if not result.healed:
        print(
            f"self-heal: proposed fix did not verify (fixed={result.fixed}, safety_passed={result.safety_passed}); needs a human."
        )
        raise SystemExit(1)

    print(f"self-heal: verified fix — {result.explanation}")
    for edit in result.edits:
        print(f"  - {edit.path}")

    if not args.branch:
        return

    from .commit import commit_to_branch

    commit_to_branch(repo_root, args.branch, result)
    print(f"self-heal: committed to branch '{args.branch}'.")

    if args.repo:
        from .post import open_draft_pr

        open_draft_pr(
            args.repo,
            args.branch,
            args.base,
            title=f"self-heal: {result.explanation}"[:72],
            body=f"Automated fix, verified against `{args.cmd}`"
            + (f" and `{args.safety_cmd}`" if args.safety_cmd else "")
            + f".\n\n{result.explanation}\n\n_This is an automated draft — a human review is still required before merge._",
        )
        print(
            f"self-heal: opened draft PR for '{args.branch}' against '{args.base}' in {args.repo}."
        )


if __name__ == "__main__":
    main()
