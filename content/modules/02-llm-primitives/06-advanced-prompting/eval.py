"""Eval: self-consistency @ n=5 must score >= 0.85 on the problem set."""
import os
import sys

THRESHOLD = 0.85


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skip: ANTHROPIC_API_KEY not set")
        return 1
    from solution import PROBLEMS, self_consistency
    from anthropic import Anthropic
    client = Anthropic()
    correct = sum(self_consistency(client, q, n=5) == g for q, g in PROBLEMS)
    acc = correct / len(PROBLEMS)
    print(f"accuracy={acc:.2f} threshold={THRESHOLD}")
    return 0 if acc >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
