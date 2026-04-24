"""Anthropic tool_use -> Pydantic structured summary.

We force Claude to emit a single tool call whose input validates against
`FilingSummary`. This is stricter than JSON mode: the model can't drift on
field names or types, and we get a ValidationError fast when it does.
"""

from __future__ import annotations

import os

import anthropic
from anthropic import APIStatusError
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from schema import FilingSummary

MODEL = "claude-sonnet-4-6"
TOOL_NAME = "submit_filing_summary"

SYSTEM = (
    "You are FilingSage, a senior equity research analyst. "
    "Read the supplied 10-K excerpt and call the `submit_filing_summary` tool "
    "exactly once. Cite section headings (e.g. 'Item 1A', 'Item 7'). "
    "Do not invent numbers; leave segment fields null if the excerpt omits them."
)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, APIStatusError):
        return exc.status_code in (429, 529, 500, 502, 503, 504)
    return False


@retry(
    retry=retry_if_exception_type(APIStatusError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def _call_claude(client: anthropic.Anthropic, ticker: str, accession: str, excerpt: str):
    tool_schema = FilingSummary.model_json_schema()
    user_msg = (
        f"Ticker: {ticker}\n"
        f"Accession: {accession}\n\n"
        f"10-K excerpt (Item 1A + Item 7, truncated):\n\n{excerpt}"
    )
    return client.messages.create(
        model=MODEL,
        max_tokens=4096,
        temperature=0,
        system=SYSTEM,
        tools=[
            {
                "name": TOOL_NAME,
                "description": "Submit the structured 10-K summary.",
                "input_schema": tool_schema,
            }
        ],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": user_msg}],
    )


def summarize(ticker: str, accession: str, excerpt: str) -> FilingSummary:
    """Call Claude, validate tool_use input, return a FilingSummary."""
    api_key = os.environ["ANTHROPIC_API_KEY"]  # raises KeyError if missing — fail loud
    client = anthropic.Anthropic(api_key=api_key)

    resp = _call_claude(client, ticker, accession, excerpt)

    tool_blocks = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
    if not tool_blocks:
        raise RuntimeError(f"No tool_use block returned. stop_reason={resp.stop_reason}")
    if tool_blocks[0].name != TOOL_NAME:
        raise RuntimeError(f"Unexpected tool: {tool_blocks[0].name}")

    try:
        summary = FilingSummary.model_validate(tool_blocks[0].input)
    except ValidationError as e:
        raise RuntimeError(f"Claude returned invalid schema:\n{e}") from e

    return summary
