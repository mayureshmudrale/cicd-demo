"""CI entrypoint:

    git diff origin/main...HEAD | python -m ai.reviewmem
    python -m ai.reviewmem --diff some.patch
    python -m ai.reviewmem --repo owner/repo --pr 123   # also posts to the real PR

Reviews every hunk in the diff independently (retrieval only supplies
optional context, never gates whether a hunk gets reviewed), applies the
deterministic max-comments cap, and prints the selected findings. Only
posts a real PR comment (the one side-effecting action here) when --repo
and --pr are both given, and never when there's nothing to report.
"""

import argparse
import sys

from .corpus import load_corpus
from .diffsplit import split_into_hunks
from .gate import select_findings
from .review import review_hunk


def _read_diff(path: str | None) -> str:
    if path:
        with open(path) as handle:
            return handle.read()
    return sys.stdin.read()


def _print_findings(findings: list) -> None:
    if not findings:
        print("review-memory: no findings.")
        return
    for finding in findings:
        print(f"[{finding.severity}] {finding.location}: {finding.comment}")
        if finding.grounded_in:
            print(f"  (grounded in past comment {finding.grounded_in})")


def main() -> None:
    """Parses CLI args, reviews every hunk, prints (and optionally posts) the capped findings."""
    parser = argparse.ArgumentParser(
        description="AI code review grounded in past human comments"
    )
    parser.add_argument(
        "--diff", help="path to a unified diff file (default: read stdin)"
    )
    parser.add_argument("--max-comments", type=int, default=5)
    parser.add_argument(
        "--repo", help="owner/repo to post findings to, e.g. $GITHUB_REPOSITORY"
    )
    parser.add_argument("--pr", type=int, help="PR number to post findings to")
    args = parser.parse_args()

    corpus = load_corpus()
    diff_text = _read_diff(args.diff)

    all_findings = [
        finding
        for location, hunk_text in split_into_hunks(diff_text)
        for finding in review_hunk(location, hunk_text, corpus)
    ]
    selected = select_findings(all_findings, max_comments=args.max_comments)
    _print_findings(selected)

    if selected and args.repo and args.pr:
        from .post import format_comment, post_comment

        post_comment(args.repo, args.pr, format_comment(selected))


if __name__ == "__main__":
    main()
