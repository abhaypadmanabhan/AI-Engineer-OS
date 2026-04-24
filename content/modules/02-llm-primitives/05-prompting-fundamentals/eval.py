"""Eval: pass if few-shot lifts accuracy by >= 15 percentage points."""
import os
import sys

THRESHOLD = 0.15


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skip: ANTHROPIC_API_KEY not set")
        return 1
    from solution import classify_zero, classify_few, TICKETS
    from anthropic import Anthropic
    client = Anthropic()
    zero = sum(classify_zero(client, t) == l for t, l in TICKETS) / len(TICKETS)
    few = sum(classify_few(client, t) == l for t, l in TICKETS) / len(TICKETS)
    lift = few - zero
    print(f"zero={zero:.2f} few={few:.2f} lift={lift:+.2f} threshold={THRESHOLD}")
    return 0 if lift >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
