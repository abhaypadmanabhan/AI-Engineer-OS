"""CLI entry point for FilingSage M1.

Usage:
    uv run python main.py --ticker AAPL
    uv run python main.py --all            # iterate tickers.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fetch_filings import extract_sections, fetch_10k_text
from summarize import summarize

TICKERS_FILE = Path(__file__).parent / "tickers.txt"


def run_one(ticker: str) -> dict:
    accession, fy_end, body = fetch_10k_text(ticker)
    excerpt = extract_sections(body)
    summary = summarize(ticker, accession, excerpt)
    # Overwrite model-supplied fields that we know authoritatively.
    out = summary.model_copy(update={
        "ticker": ticker.upper(),
        "accession_number": accession,
        "fiscal_year_end": fy_end,
    })
    return out.model_dump()


def main() -> int:
    parser = argparse.ArgumentParser(description="FilingSage M1 summarizer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ticker", help="Single ticker symbol (e.g. AAPL)")
    group.add_argument("--all", action="store_true", help="Run all tickers from tickers.txt")
    args = parser.parse_args()

    if args.ticker:
        result = run_one(args.ticker)
        print(json.dumps(result, indent=2))
        return 0

    tickers = [t.strip() for t in TICKERS_FILE.read_text().splitlines() if t.strip()]
    results: dict[str, dict] = {}
    for t in tickers:
        try:
            results[t] = run_one(t)
        except Exception as e:  # noqa: BLE001
            print(f"[{t}] FAILED: {e}", file=sys.stderr)
            results[t] = {"error": str(e)}
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
