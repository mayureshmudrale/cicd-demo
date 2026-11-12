"""Phase 0 gate: run with LIVE=1 and GEMINI_API_KEY set to record the first
real Gemini call (ai/evals/cassettes/smoke/*.json). Run with neither set to
replay it afterwards, proving the cassette round-trips.

    GEMINI_API_KEY=... LIVE=1 python -m ai.smoke_test
    python -m ai.smoke_test
"""
from ai.llm import generate
from ai.schemas.smoke import SmokeTestResponse

PROMPT = (
    "Reply with strict JSON matching this schema and nothing else: "
    '{"ok": true, "note": "<ten words or fewer>"}'
)


def main() -> None:
    result = generate(feature="smoke", prompt=PROMPT, response_schema=SmokeTestResponse)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
