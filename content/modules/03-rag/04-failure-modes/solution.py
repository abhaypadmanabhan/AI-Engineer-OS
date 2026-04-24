"""Solution: walk 12 canned retrieval transcripts + tag each with a failure mode."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
TAXONOMY = {"boundary_split", "coverage_gap", "redundancy", "numeric_exact"}


def main() -> None:
    cases = json.loads((DATA / "transcripts.json").read_text())
    covered: set[str] = set()
    for c in cases:
        print(f"Q: {c['query']}")
        for r in c["top_k"]:
            print(f"   [{r['doc_id']}] {r['text'][:70]}...")
        print(f"   → {c['failure_mode']}")
        print()
        covered.add(c["failure_mode"])

    print(f"categories_covered={sorted(covered)}")
    print(f"failures_identified={len(covered & TAXONOMY)}")


if __name__ == "__main__":
    main()
