"""Eval: pass if the learner's (actual, guess) pairs hit ≥ 0.9 within-10pct."""
import sys
import json

THRESHOLD = 0.9


def main() -> int:
    # Expect a JSON file path as arg with list of {actual, guess}
    path = sys.argv[1] if len(sys.argv) > 1 else "report.json"
    try:
        rows = json.load(open(path))
    except Exception as e:
        print(f"could not read {path}: {e}")
        return 1
    if not rows:
        print("no rows")
        return 1
    hits = sum(1 for r in rows if abs(r["actual"] - r["guess"]) / r["actual"] <= 0.10)
    frac = hits / len(rows)
    print(f"within_10pct={frac:.3f} threshold={THRESHOLD}")
    return 0 if frac >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
