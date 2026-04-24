"""Eval: fetch 100 HN stories, require throughput >= 20 req/s."""
from __future__ import annotations
import asyncio
import sys
from solution import benchmark

THRESHOLD_RPS = 20.0


def main() -> int:
    count, elapsed, rps = asyncio.run(benchmark(100))
    print(f"count={count} elapsed={elapsed:.2f}s rps={rps:.1f}")
    if count < 100:
        print(f"FAIL: only fetched {count}/100", file=sys.stderr)
        return 1
    if rps < THRESHOLD_RPS:
        print(f"FAIL: rps {rps:.1f} < threshold {THRESHOLD_RPS}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
