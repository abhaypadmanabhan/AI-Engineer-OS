"""Solution: measure few-shot lift over zero-shot on 20 labeled tickets."""
import os
from anthropic import Anthropic

TICKETS = [
    ("My card was charged twice this month.", "billing"),
    ("The app crashes when I open settings.", "bug"),
    ("Please add a dark mode toggle.", "feature"),
    ("I cannot log in, password reset emails never arrive.", "account"),
    ("Unrelated question: what's your return policy?", "other"),
    ("Refund for the duplicate charge on 4/12 please.", "billing"),
    ("Export to CSV throws a 500 error.", "bug"),
    ("Add SSO with Okta.", "feature"),
    ("My account got locked after 3 tries, unlock it.", "account"),
    ("Just saying hi to the team.", "other"),
    ("Why was I billed $29 instead of $19?", "billing"),
    ("The iOS app freezes on splash screen.", "bug"),
    ("Feature request: keyboard shortcut for new ticket.", "feature"),
    ("Change my email from a@x.com to b@x.com.", "account"),
    ("Weather is nice today.", "other"),
    ("Cancel my subscription and refund prorated amount.", "billing"),
    ("404 on /api/v2/users endpoint.", "bug"),
    ("Would love a mobile widget.", "feature"),
    ("I forgot which email I signed up with.", "account"),
    ("Random feedback: the logo is nice.", "other"),
]

SYSTEM = """You are a support ticket classifier. Output only one of:
billing, bug, feature, account, other.
Do not add explanation."""

EXAMPLES = """<example>
<ticket>My card was charged twice.</ticket>
<category>billing</category>
</example>
<example>
<ticket>The app crashes when I open settings.</ticket>
<category>bug</category>
</example>
<example>
<ticket>Add dark mode please.</ticket>
<category>feature</category>
</example>
<example>
<ticket>I cannot log in since the update.</ticket>
<category>account</category>
</example>"""


def classify_zero(client: Anthropic, ticket: str) -> str:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user",
                   "content": f"Classify as billing, bug, feature, account, or other:\n{ticket}"}],
    )
    return r.content[0].text.strip().lower().split()[0].rstrip(".,")


def classify_few(client: Anthropic, ticket: str) -> str:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        temperature=0,
        system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"{EXAMPLES}\n<ticket>{ticket}</ticket>\n<category>"}],
    )
    return r.content[0].text.strip().lower().split()[0].rstrip(".,</>")


def accuracy(fn, client) -> float:
    hits = 0
    for text, label in TICKETS:
        pred = fn(client, text)
        hits += int(pred == label)
    return hits / len(TICKETS)


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    client = Anthropic()
    zero = accuracy(classify_zero, client)
    few = accuracy(classify_few, client)
    lift = few - zero
    print(f"zero_shot={zero:.2f} few_shot={few:.2f} lift={lift:+.2f}")


if __name__ == "__main__":
    main()
