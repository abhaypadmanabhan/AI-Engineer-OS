"""Reference: Python equivalent of the promptfoo 4-prompt bakeoff.

Useful when you want to call the same matrix from a notebook or CI step
without invoking the npm CLI."""
import os
from anthropic import Anthropic

TICKETS = [
    ("My card was charged twice this month.", "billing"),
    ("The app crashes when I open settings.", "bug"),
    ("Add dark mode please.", "feature"),
    ("I cannot log in since yesterday's update.", "account"),
    ("Refund for the duplicate charge please.", "billing"),
    ("Export to CSV throws 500.", "bug"),
    ("Add SSO with Okta.", "feature"),
    ("Unlock my account after failed logins.", "account"),
    ("Why was I billed $29 instead of $19?", "billing"),
    ("iOS app freezes on splash screen.", "bug"),
]

ZERO_SHOT = "Classify as billing, bug, feature, account, or other:\n{t}"

FEW_SHOT = """Classify as one of: billing, bug, feature, account, other.
Examples:
- 'card charged twice' -> billing
- 'app crashes' -> bug
- 'add dark mode' -> feature
- 'cannot log in' -> account

Ticket: {t}
Category:"""

COT = """Classify the ticket. Think briefly, then give the final label.
Ticket: {t}"""

COT_DELIM = """Classify the ticket as billing, bug, feature, account, or other.
<reasoning> briefly explain </reasoning>
<answer> one word </answer>
Ticket: {t}"""

PROMPTS = {"zero_shot": ZERO_SHOT, "few_shot": FEW_SHOT,
           "cot": COT, "cot_delim": COT_DELIM}


def run_prompt(client: Anthropic, tmpl: str, ticket: str) -> str:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=60,
        temperature=0,
        messages=[{"role": "user", "content": tmpl.format(t=ticket)}],
    )
    text = r.content[0].text.lower()
    if "<answer>" in text:
        text = text.split("<answer>")[1].split("</answer>")[0]
    for cat in ("billing", "bug", "feature", "account", "other"):
        if cat in text:
            return cat
    return "other"


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    client = Anthropic()
    for name, tmpl in PROMPTS.items():
        correct = sum(run_prompt(client, tmpl, t) == lbl for t, lbl in TICKETS)
        print(f"{name:12s} pass_rate={correct/len(TICKETS):.2f}")


if __name__ == "__main__":
    main()
