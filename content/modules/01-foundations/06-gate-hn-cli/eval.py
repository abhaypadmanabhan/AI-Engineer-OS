"""Eval: run solution CLI, parse JSON, re-validate; require >= LIMIT rows."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

from solution import Story
from pydantic import ValidationError

LIMIT = 20
HERE = Path(__file__).parent


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(HERE / "solution.py"), "top", "--limit", str(LIMIT), "--json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        print(f"FAIL: CLI exit {proc.returncode}", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 1
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        print(f"FAIL: invalid JSON from CLI: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print("FAIL: expected list", file=sys.stderr)
        return 1
    ok = 0
    for row in data:
        try:
            Story.model_validate(row)
            ok += 1
        except ValidationError:
            pass
    print(f"stories_returned_valid_json={ok}/{LIMIT}")
    if ok < LIMIT:
        print(f"FAIL: only {ok} valid, need {LIMIT}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
