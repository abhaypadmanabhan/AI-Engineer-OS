"""Eval: the best prompt in the matrix must pass >= 0.9."""
import os
import sys

THRESHOLD = 0.9


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skip: ANTHROPIC_API_KEY not set")
        return 1
    from solution import PROMPTS, TICKETS, run_prompt
    from anthropic import Anthropic
    client = Anthropic()
    best = 0.0
    best_name = ""
    for name, tmpl in PROMPTS.items():
        acc = sum(run_prompt(client, tmpl, t) == lbl for t, lbl in TICKETS) / len(TICKETS)
        print(f"{name:12s} acc={acc:.2f}")
        if acc > best:
            best, best_name = acc, name
    print(f"winner={best_name} acc={best:.2f} threshold={THRESHOLD}")
    return 0 if best >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
