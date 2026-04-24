"""Layer 2 exit solution: 12-class ticket classifier via tool use + few-shot."""
import os
import json
from pathlib import Path
from typing import Literal
from anthropic import Anthropic
from pydantic import BaseModel

Category = Literal[
    "billing", "bug", "feature", "account", "security", "performance",
    "integration", "documentation", "refund", "outage", "abuse", "other",
]


class Prediction(BaseModel):
    category: Category


TOOL = {
    "name": "classify_ticket",
    "description": "Assign one category to a support ticket.",
    "input_schema": Prediction.model_json_schema(),
}

SYSTEM = """You are a triage bot for a SaaS support queue.
Categories and when to use them:
- billing: charges, invoices, plan changes (not refunds)
- bug: something broken or erroring
- feature: request for new functionality
- account: login, email, username, merges (non-security)
- security: 2FA, suspicious logins, vulnerabilities, account takeover
- performance: slow responses, timeouts, latency regressions (not outages)
- integration: third-party connectors (Slack, Jira, Zapier, CRM)
- documentation: docs wrong, missing, or outdated
- refund: explicit refund request
- outage: whole service or region down
- abuse: user-to-user harassment, spam, NSFW, scams
- other: greetings, feedback, unrelated

Pick exactly one."""

EXAMPLES = """<example>
<ticket>My card was charged twice — refund the duplicate.</ticket>
<category>billing</category>
</example>
<example>
<ticket>Please refund last month — we didn't use it.</ticket>
<category>refund</category>
</example>
<example>
<ticket>I think someone signed into my account from Russia.</ticket>
<category>security</category>
</example>
<example>
<ticket>Your API is returning 503s since 14:00 UTC.</ticket>
<category>outage</category>
</example>"""


def classify(client: Anthropic, text: str) -> str:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=60,
        temperature=0,
        system=SYSTEM,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "classify_ticket"},
        messages=[{"role": "user",
                   "content": f"{EXAMPLES}\n<ticket>{text}</ticket>"}],
    )
    call = next(b for b in r.content if b.type == "tool_use")
    return Prediction.model_validate(call.input).category


def run_eval(path: str | None = None) -> float:
    client = Anthropic()
    p = Path(path) if path else Path(__file__).parent / "data" / "tickets.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    hits, total = 0, len(rows)
    for row in rows:
        pred = classify(client, row["text"])
        ok = pred == row["category"]
        hits += int(ok)
        if not ok:
            print(f"MISS id={row['id']} gold={row['category']} pred={pred} :: {row['text'][:60]}")
    acc = hits / total
    print(f"accuracy={acc:.3f} ({hits}/{total})")
    return acc


if __name__ == "__main__":
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    run_eval()
