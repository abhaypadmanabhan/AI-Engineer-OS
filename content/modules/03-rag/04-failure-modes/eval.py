"""Eval: all 4 failure-mode categories present in transcripts.json."""
import json
import sys
from pathlib import Path

THRESHOLD = 4
TAXONOMY = {"boundary_split", "coverage_gap", "redundancy", "numeric_exact"}


def main() -> int:
    data = Path(__file__).parent / "data" / "transcripts.json"
    cases = json.loads(data.read_text())
    covered = {c["failure_mode"] for c in cases} & TAXONOMY
    score = len(covered)
    print(f"failures_identified={score} threshold={THRESHOLD} covered={sorted(covered)}")
    return 0 if score >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
