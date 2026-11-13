"""Given a failing command's real output and the current content of the
files it implicates, asks Gemini for a full-file rewrite that fixes it.

No deterministic fallback makes sense for patch generation itself — there
is no safe guess at a code fix, unlike every other feature's fallback in
this repo. GeminiUnavailable means "needs a human," surfaced by returning
None rather than inventing a change. The real safety net isn't here
anyway: it's apply.py's verification, which never trusts this proposal
on Gemini's word alone.
"""

from ai.llm import GeminiUnavailable, generate

from .schemas import PatchProposal

PROMPT_TEMPLATE = """A CI command failed:

Command: {command}

Output:
{output}

Current content of the implicated file(s):
{files_block}

Propose the SMALLEST change that fixes this failure without changing any
unrelated behavior. For each file that actually needs to change, give
its COMPLETE new content (not a diff) — only include files you're
actually changing.

Reply with strict JSON: {{"explanation": "<one or two sentences>", "edits": [{{"path": "<file path exactly as given above>", "new_content": "<the file's complete new content>"}}]}}
"""


def _format_files(files: dict[str, str]) -> str:
    return "\n\n".join(f"--- {path} ---\n{content}" for path, content in files.items())


def propose_fix(
    command: str, output: str, files: dict[str, str]
) -> PatchProposal | None:
    """Returns a proposal, or None if no live call could be made."""
    prompt = PROMPT_TEMPLATE.format(
        command=command, output=output, files_block=_format_files(files)
    )
    try:
        return generate(
            feature="selfheal", prompt=prompt, response_schema=PatchProposal
        )
    except GeminiUnavailable as exc:
        print(f"TEMP DIAGNOSTIC propose_fix GeminiUnavailable: {exc}")
        return None
