"""Reviews one code hunk for genuine issues. Retrieval (retrieve.py) finds
similar past review comments and passes them in as optional context —
every hunk still gets its own independent review regardless of whether
anything similar was found; Gemini is never limited to only re-surfacing
history.

AI proposes, deterministic code disposes: Gemini drafts candidate
findings here; gate.py's select_findings() caps what actually gets
posted.
"""

import logging

from ai.llm import GeminiUnavailable, generate

from .corpus import GoldenComment
from .retrieve import confident_match, top_matches
from .schemas import ReviewFinding, _ReviewResponse

logger = logging.getLogger("ai-reviewmem")

PROMPT_TEMPLATE = """You are reviewing one code hunk from a pull request diff.

Hunk ({location}):
{hunk}

{context_block}

List concrete, genuine issues with this code: correctness bugs, security
risks, or maintainability problems a careful reviewer would flag. Do not
invent issues that aren't really there — if the code is fine, return an
empty list. You are not limited to the past patterns above; flag anything
real you see. For each issue, set "grounded_in" to the id of a past
comment above ONLY if it's genuinely the same concern on similar code;
otherwise leave it null — don't force a citation that doesn't fit.

Reply with strict JSON: {{"findings": [{{"severity": "low"|"medium"|"high", "category": "<short label>", "comment": "<the review comment to post, addressed to this code>", "grounded_in": "<a past comment id from above, or null>"}}]}}
"""


def _format_context(matches: list[GoldenComment]) -> str:
    if not matches:
        return "No similar past review comments found for this code."
    lines = [
        "Similar past review comments from this codebase's own history (context, not a checklist):"
    ]
    lines.extend(
        f'- [{match.id}] on similar code: "{match.comment}"' for match in matches
    )
    return "\n".join(lines)


def _fallback_findings(
    location: str, hunk_text: str, corpus: list[GoldenComment]
) -> list[ReviewFinding]:
    """No live judgment call possible, so no judgment call is made: only
    surface a historical match that clears `confident_match`'s much
    stricter bar. A wrong citation with no way to double-check it is
    worse than silence — this is not the same list `top_matches` builds
    for context, which a live call can freely disregard."""
    best = confident_match(hunk_text, corpus)
    if best is None:
        return []
    return [
        ReviewFinding(
            location=location,
            severity="medium",
            category=best.category,
            comment=f"(fallback, no live review) similar past feedback: {best.comment}",
            grounded_in=best.id,
        )
    ]


def review_hunk(
    location: str, hunk_text: str, corpus: list[GoldenComment]
) -> list[ReviewFinding]:
    """Returns the findings Gemini proposes for one hunk; empty if none."""
    matches = top_matches(hunk_text, corpus)
    prompt = PROMPT_TEMPLATE.format(
        location=location, hunk=hunk_text, context_block=_format_context(matches)
    )

    try:
        result = generate(
            feature="reviewmem", prompt=prompt, response_schema=_ReviewResponse
        )
    except GeminiUnavailable as exc:
        logger.warning("review falling back to historical match only: %s", exc)
        return _fallback_findings(location, hunk_text, corpus)

    return [
        ReviewFinding(location=location, **finding.model_dump())
        for finding in result.findings
    ]
