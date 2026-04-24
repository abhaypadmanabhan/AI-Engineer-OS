"""Solution: count tokens for 10 prompts, compare to char/4 heuristic."""
import os
from anthropic import Anthropic

PROMPTS = [
    "Summarize this 10-K in three bullets.",
    "def classify_ticket(text: str) -> Ticket: ...",
    "Translate to French: The quick brown fox jumps over the lazy dog.",
    "Write a SQL query joining users and orders on user_id.",
    "Explain transformer attention in one paragraph.",
    "curl -X POST https://api.anthropic.com/v1/messages -H 'x-api-key: $KEY'",
    "Return JSON: {name, email, signup_date} from the text below.",
    "Refactor this Python to use asyncio.gather for the HTTP calls.",
    "Pourquoi l'IA est-elle si utile pour les developpeurs?",
    "import numpy as np\nimport pandas as pd\nfrom typing import Literal",
]


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    client = Anthropic()
    within = 0
    for p in PROMPTS:
        r = client.messages.count_tokens(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": p}],
        )
        actual = r.input_tokens
        guess = max(1, len(p) // 4)
        err = abs(actual - guess) / actual
        ok = err <= 0.10
        within += int(ok)
        print(f"actual={actual:3d} guess={guess:3d} err={err:.2%} ok={ok}  :: {p[:40]}")
    frac = within / len(PROMPTS)
    print(f"within_10pct_fraction={frac:.2f}")


if __name__ == "__main__":
    main()
