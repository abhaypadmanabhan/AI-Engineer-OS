"""Eval: schema must reject >= 95% of malformed payloads and accept the valid one."""
from __future__ import annotations
import sys
from solution import accept_valid, reject_rate

THRESHOLD = 0.95


def main() -> int:
    rr = reject_rate()
    ok = accept_valid()
    print(f"reject_rate={rr:.2f} valid_accepted={ok}")
    if not ok:
        print("FAIL: valid payload was rejected", file=sys.stderr)
        return 1
    if rr < THRESHOLD:
        print(f"FAIL: reject_rate {rr:.2f} < {THRESHOLD}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
