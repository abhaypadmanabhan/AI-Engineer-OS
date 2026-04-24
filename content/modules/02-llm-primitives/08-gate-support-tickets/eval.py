"""Layer 2 gate: accuracy >= 0.88 on data/tickets.jsonl."""
import os
import sys

THRESHOLD = 0.88


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skip: ANTHROPIC_API_KEY not set")
        return 1
    from solution import run_eval
    acc = run_eval()
    print(f"gate_metric=ticket_classification_accuracy value={acc:.3f} threshold={THRESHOLD}")
    return 0 if acc >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
