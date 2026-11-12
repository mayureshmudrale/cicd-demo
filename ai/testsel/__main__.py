"""CI entrypoint:

    python -m ai.testsel --base <ref> --head <ref> --test-root app/backend/tests

Computes the changed-file list via `git diff --name-only`, finds the
available test files under --test-root, runs `select()`, and prints the
selected test paths (one per line, relative to the repo root) with a
leading `# <reasoning>` comment line, for ci.yml to pass to pytest.
"""
import argparse
import glob
import subprocess

from .select import select


def changed_files(base: str, head: str) -> list[str]:
    """Files that differ between `base` and `head` (git diff's three-dot range)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> None:
    """Parses CLI args, runs `select`, prints the chosen tests for ci.yml to consume."""
    parser = argparse.ArgumentParser(
        description="Pick which tests to run for a PR's changed files"
    )
    parser.add_argument("--base", required=True, help="base ref/sha to diff against")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--test-root", default="app/backend/tests")
    args = parser.parse_args()

    all_py_files = glob.glob(f"{args.test_root}/**/*.py", recursive=True)
    # conftest.py isn't a test module pytest can be told to "run" on its
    # own — it's fixtures, always loaded implicitly by whatever test files
    # *are* selected.
    available = sorted(f for f in all_py_files if f.rsplit("/", 1)[-1] != "conftest.py")

    # An unresolvable base ref (shallow clone, rebased/deleted branch, no
    # PR context at all) means "we don't know what changed" — same unsafe
    # failure mode as GeminiUnavailable, so it gets the same safe default.
    try:
        diff = changed_files(args.base, args.head)
    except subprocess.CalledProcessError as exc:
        print(
            f"# could not compute a diff against {args.base!r} ({exc}); "
            "running every test to stay safe"
        )
        for test in available:
            print(test)
        return

    result = select(diff, available)
    print(f"# {result.reasoning}")
    for test in result.selected_tests:
        print(test)


if __name__ == "__main__":
    main()
