"""M1 auto-grader.

Runs against either:
    1. A checked-in `sample_output.json` (fast, no network/API), OR
    2. A live `main.py --ticker AAPL` run if ANTHROPIC_API_KEY is set and
       `--live` is passed.

Checks:
    - Output parses as `FilingSummary`
    - len(top_risk_factors) >= 3
    - len(citations) >= 1
    - management_outlook is non-empty
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from pydantic import ValidationError

from schema import FilingSummary

HERE = Path(__file__).parent
SAMPLE = HERE / "sample_output.json"


def load_payload(live: bool, ticker: str) -> dict:
    if live:
        proc = subprocess.run(
            [sys.executable, str(HERE / "main.py"), "--ticker", ticker],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)
    if not SAMPLE.exists():
        raise FileNotFoundError(
            f"{SAMPLE} missing. Run `python main.py --ticker AAPL > sample_output.json` once."
        )
    return json.loads(SAMPLE.read_text())


def check(payload: dict) -> list[str]:
    errors: list[str] = []
    try:
        summary = FilingSummary.model_validate(payload)
    except ValidationError as e:
        return [f"schema validation failed: {e}"]

    if len(summary.top_risk_factors) < 3:
        errors.append(f"top_risk_factors < 3 (got {len(summary.top_risk_factors)})")
    if len(summary.citations) < 1:
        errors.append("citations empty")
    if not summary.management_outlook.strip():
        errors.append("management_outlook empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Call main.py live")
    parser.add_argument("--ticker", default="AAPL")
    args = parser.parse_args()

    payload = load_payload(args.live, args.ticker)
    errors = check(payload)
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
