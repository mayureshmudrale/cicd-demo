"""Test selection (feature #6): given the files a PR changed, picks which
test files are worth running, so CI doesn't have to run the full suite on
every change.

"AI proposes, deterministic code disposes" applies two ways here:
  - a deterministic floor always runs: any test file whose name directly
    maps to a changed source file (foo.py -> test_foo.py) is never left to
    the AI's judgment, and anything the AI names that isn't a real test
    file is dropped.
  - the unsafe failure mode for this feature is skipping a test that
    mattered, not running an extra one — so GeminiUnavailable falls back
    to running every test, not to running none.
"""
import logging

from ai.llm import GeminiUnavailable, generate

from .schemas import TestSelection

logger = logging.getLogger("ai-testsel")

PROMPT_TEMPLATE = """A pull request changed these files:

{changed_files}

Here is the full list of available test files:

{available_tests}

Decide which of the available test files are worth running to validate
this change, beyond the obvious direct ones (already handled separately).
Consider indirect impact: a change to a shared config, schema, or client
module can affect tests that don't share its name.

Reply with strict JSON: {{"selected_tests": [<subset of the available test files above, can be empty>], "reasoning": "<one or two sentences>"}}
"""


def _stem(path: str) -> str:
    return path.rsplit("/", 1)[-1].removesuffix(".py")


def _direct_matches(changed_files: list[str], available_tests: list[str]) -> set[str]:
    """Deterministic floor: a changed foo.py always pulls in test_foo.py
    (or foo_test.py), regardless of what the AI decides."""
    changed_stems = {_stem(path) for path in changed_files}
    matches = set()
    for test in available_tests:
        test_subject = _stem(test).removeprefix("test_").removesuffix("_test")
        if test_subject in changed_stems:
            matches.add(test)
    return matches


def select(changed_files: list[str], available_tests: list[str]) -> TestSelection:
    """Returns the test files to run for this change."""
    direct = _direct_matches(changed_files, available_tests)

    prompt = PROMPT_TEMPLATE.format(
        changed_files="\n".join(changed_files),
        available_tests="\n".join(available_tests),
    )
    try:
        ai_pick = generate(
            feature="testsel", prompt=prompt, response_schema=TestSelection
        )
    except GeminiUnavailable as exc:
        logger.warning("test selection falling back to running all tests: %s", exc)
        return TestSelection(
            selected_tests=sorted(available_tests),
            reasoning=(
                f"fallback (Gemini unavailable: {exc}); running every test to stay safe"
            ),
        )

    valid_ai_picks = {
        test for test in ai_pick.selected_tests if test in available_tests
    }
    return TestSelection(
        selected_tests=sorted(direct | valid_ai_picks), reasoning=ai_pick.reasoning
    )
