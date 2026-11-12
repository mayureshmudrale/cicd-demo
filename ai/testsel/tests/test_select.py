import sys

from ai.llm import GeminiUnavailable
from ai.testsel.schemas import TestSelection
from ai.testsel.select import select

select_module = sys.modules["ai.testsel.select"]

AVAILABLE_TESTS = [
    "app/backend/tests/test_main.py",
    "app/backend/tests/test_faults.py",
    "app/backend/tests/test_config.py",
]


def test_gemini_unavailable_falls_back_to_running_everything(monkeypatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(select_module, "generate", raise_unavailable)

    result = select(["app/backend/main.py"], AVAILABLE_TESTS)
    assert result.selected_tests == sorted(AVAILABLE_TESTS)
    assert "fallback" in result.reasoning


def test_direct_match_included_even_if_ai_omits_it(monkeypatch):
    monkeypatch.setattr(
        select_module,
        "generate",
        lambda **kwargs: TestSelection(
            selected_tests=[], reasoning="nothing indirectly affected"
        ),
    )

    result = select(["app/backend/main.py"], AVAILABLE_TESTS)
    assert "app/backend/tests/test_main.py" in result.selected_tests


def test_hallucinated_test_file_is_dropped(monkeypatch):
    monkeypatch.setattr(
        select_module,
        "generate",
        lambda **kwargs: TestSelection(
            selected_tests=[
                "app/backend/tests/test_config.py",
                "app/backend/tests/test_nonexistent.py",
            ],
            reasoning="config changed, plus a guess",
        ),
    )

    result = select(["app/backend/config.py"], AVAILABLE_TESTS)
    assert "app/backend/tests/test_nonexistent.py" not in result.selected_tests
    assert "app/backend/tests/test_config.py" in result.selected_tests
