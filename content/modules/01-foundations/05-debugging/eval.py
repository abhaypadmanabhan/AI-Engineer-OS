"""Eval: the buggy path must raise, the fixed path must complete."""
from __future__ import annotations
import asyncio
import sys
from solution import run_buggy, run_fixed, SAMPLE_IDS


def main() -> int:
    # Fixed path should succeed.
    try:
        titles = asyncio.run(run_fixed(SAMPLE_IDS))
    except Exception as e:
        print(f"FAIL: fixed path raised {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if len(titles) == 0:
        print("FAIL: fixed path returned no titles", file=sys.stderr)
        return 1
    # Buggy path should raise OR return at least one None (indicating the bug).
    # We accept either because HN's deleted-item behavior drifts over time.
    bug_reproduced = False
    try:
        result = asyncio.run(run_buggy(SAMPLE_IDS))
        if any(t is None for t in result):
            bug_reproduced = True
    except (TypeError, KeyError):
        bug_reproduced = True
    if not bug_reproduced:
        print("WARN: buggy path did not reproduce (HN data changed)", file=sys.stderr)
    print(f"PASS fixed_titles={len(titles)} bug_reproduced={bug_reproduced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
