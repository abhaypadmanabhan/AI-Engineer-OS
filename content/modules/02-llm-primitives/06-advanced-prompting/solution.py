"""Solution: self-consistency at n=5 on a small math set."""
import os
import re
from collections import Counter
from anthropic import Anthropic

PROBLEMS = [
    ("A bookstore sold 42 books on Monday, twice that on Tuesday, and 15 fewer than Tuesday on Wednesday. Total?", 195),
    ("3x + 7 = 22. Solve for x.", 5),
    ("A train covers 120 km in 2 hours. Speed in km/h?", 60),
    ("What is 17 * 23?", 391),
    ("Sum of first 10 positive integers?", 55),
    ("12% of 250 is?", 30),
    ("If a rectangle has length 9 and width 6, what's its area?", 54),
    ("2^10 equals?", 1024),
    ("A shirt costs $40 after a 20% discount. Original price?", 50),
    ("Sally has 3 times as many apples as Tom. Together they have 48. How many does Tom have?", 12),
]


def one_sample(client: Anthropic, q: str, temperature: float) -> int | None:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        temperature=temperature,
        messages=[
            {"role": "user", "content": q + " Reason briefly, then end with </reasoning> followed by the numeric answer only."},
            {"role": "assistant", "content": "<reasoning>\n"},
        ],
    )
    text = "<reasoning>\n" + r.content[0].text
    tail = text.split("</reasoning>")[-1]
    m = re.search(r"-?\d+", tail)
    return int(m.group(0)) if m else None


def self_consistency(client: Anthropic, q: str, n: int = 5) -> int | None:
    answers = [one_sample(client, q, 0.8) for _ in range(n)]
    answers = [a for a in answers if a is not None]
    if not answers:
        return None
    winner, _ = Counter(answers).most_common(1)[0]
    return winner


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    client = Anthropic()
    correct = 0
    for q, gold in PROBLEMS:
        pred = self_consistency(client, q, n=5)
        ok = pred == gold
        correct += int(ok)
        print(f"pred={pred} gold={gold} ok={ok} :: {q[:60]}")
    acc = correct / len(PROBLEMS)
    print(f"self_consistency_accuracy={acc:.2f}")


if __name__ == "__main__":
    main()
