"""Thin Gemini client shared by every AI feature.

Core rule the whole platform leans on: AI proposes, deterministic code
disposes. This module only gets a validated, schema-shaped answer out of
Gemini (or out of a recorded cassette) — every feature's own deterministic
guard lives in its own module, not here.
"""
import os
import time
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from .cassette import cassette_key, load_cassette, save_cassette
from .redact import redact

T = TypeVar("T", bound=BaseModel)

PROMPT_VERSION = "v1"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
DEFAULT_TIMEOUT_S = int(os.environ.get("GEMINI_TIMEOUT_S", "20"))
DEFAULT_MAX_OUTPUT_TOKENS = 2048
CALL_BUDGET_PER_RUN = int(os.environ.get("GEMINI_CALL_BUDGET", "20"))


class GeminiUnavailable(Exception):
    """No live call could be made and no cassette matched.

    Callers must catch this and take their feature's deterministic fallback
    path (e.g. static canary steps, skip-the-PR-comment) rather than block.
    """


class _CallBudget:
    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def take(self) -> None:
        if self.used >= self.limit:
            raise GeminiUnavailable(f"per-run call budget of {self.limit} exhausted")
        self.used += 1


_budget = _CallBudget(CALL_BUDGET_PER_RUN)


def generate(
    *,
    feature: str,
    prompt: str,
    response_schema: Type[T],
    prompt_version: str = PROMPT_VERSION,
    model: str = DEFAULT_MODEL,
) -> T:
    """Returns a validated `response_schema` instance from Gemini (or a cassette).

    Default (LIVE unset): replays `ai/evals/cassettes/<feature>/<key>.json`;
    raises GeminiUnavailable if none exists yet.
    LIVE=1: calls Gemini for real (temperature 0, timeout, token cap, one
    retry on invalid JSON), then records the cassette for next time.
    """
    clean_prompt = redact(prompt)
    key = cassette_key(
        feature=feature,
        prompt=clean_prompt,
        schema=response_schema.__name__,
        prompt_version=prompt_version,
    )

    if os.environ.get("LIVE") != "1":
        cached = load_cassette(feature, key)
        if cached is None:
            raise GeminiUnavailable(f"no cassette for {feature}/{key}; set LIVE=1 to record one")
        return response_schema.model_validate(cached["response"])

    _budget.take()

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            raw = _call_live(clean_prompt, model=model)
            parsed = response_schema.model_validate_json(raw)
            save_cassette(feature, key, request=clean_prompt, response=parsed.model_dump())
            return parsed
        except ValidationError as exc:
            last_error = exc
            continue
        except _RateLimited:
            if attempt == 0:
                time.sleep(2)
                continue
            raise GeminiUnavailable("rate limited after retry") from None
        except Exception as exc:  # network error, timeout, auth failure, ...
            raise GeminiUnavailable(str(exc)) from exc

    raise GeminiUnavailable(f"schema validation failed twice: {last_error}")


class _RateLimited(Exception):
    pass


def _call_live(prompt: str, *, model: str) -> str:
    # NOTE: kwargs here target the `google-genai` SDK; check them against
    # whatever version ends up pinned before relying on this in CI.
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiUnavailable("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT_S * 1000),
            ),
        )
    except ClientError as exc:
        if getattr(exc, "code", None) == 429:
            raise _RateLimited from exc
        raise

    return response.text
