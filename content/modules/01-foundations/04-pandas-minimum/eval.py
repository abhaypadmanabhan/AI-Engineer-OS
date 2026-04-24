"""Eval: groupby correctness on the cached HN CSV.

Pass iff:
  - sum of per-author story counts equals total non-null authors
  - total_score column is Int64 / numeric and non-negative
  - to_records emits no NaN (JSON-clean)
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
from solution import write_sample, load, by_author, to_records, CSV


def main() -> int:
    if not CSV.exists():
        write_sample()
    df = load()
    g = by_author(df)
    total_authored = int(df["by"].dropna().shape[0])
    grouped_sum = int(g["stories"].sum())
    if grouped_sum != total_authored:
        print(f"FAIL: grouped sum {grouped_sum} != total {total_authored}", file=sys.stderr)
        return 1
    if (g["total_score"] < 0).any():
        print("FAIL: negative total_score", file=sys.stderr)
        return 1
    recs = to_records(df.head(10))
    blob = json.dumps(recs, default=str)
    if "NaN" in blob:
        print("FAIL: NaN leaked into records", file=sys.stderr)
        return 1
    # round-trip: make sure every record is JSON-serializable
    for r in recs:
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                print(f"FAIL: NaN in key {k}", file=sys.stderr)
                return 1
    print(f"PASS grouped_sum={grouped_sum} total={total_authored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
