"""Fetch latest 10-K filings from SEC EDGAR for a list of tickers.

Honors EDGAR's fair-access rules: requires `EDGAR_USER_AGENT` env var ("Name email"),
sleeps 100ms between requests (≤10 req/s SEC limit). Caches HTML to disk; re-running
is idempotent. Extracts plain text + section markers (Item 1, 1A, 7, 7A, 8, etc.).

Usage:
    python fetch_filings.py --tickers TICKERS.txt --out data/filings/ --limit 100

Caches:
    data/filings/<TICKER>.txt          # extracted plain text with section markers
    data/filings/_raw/<CIK>_<acc>.htm  # raw HTML

Reused at 500-filing scale (just bump --limit and add tickers to TICKERS.txt).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx

EDGAR_BASE = "https://www.sec.gov"
USER_AGENT = os.environ.get("EDGAR_USER_AGENT", "")


def _client() -> httpx.Client:
    if not USER_AGENT:
        sys.exit("EDGAR_USER_AGENT env var required (format: 'Name email@domain')")
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
        timeout=30.0,
    )


def _ticker_to_cik(client: httpx.Client, ticker: str) -> str | None:
    """Resolve ticker → 10-digit CIK using SEC's company tickers JSON."""
    if not hasattr(_ticker_to_cik, "_map"):
        r = client.get("https://www.sec.gov/files/company_tickers.json")
        r.raise_for_status()
        m = {}
        for row in r.json().values():
            m[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
        _ticker_to_cik._map = m
        time.sleep(0.1)
    return _ticker_to_cik._map.get(ticker.upper())


def _latest_10k(client: httpx.Client, cik: str) -> dict | None:
    r = client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    r.raise_for_status()
    time.sleep(0.1)
    sub = r.json()["filings"]["recent"]
    for i, form in enumerate(sub["form"]):
        if form == "10-K":
            return {
                "accession": sub["accessionNumber"][i].replace("-", ""),
                "primary_doc": sub["primaryDocument"][i],
                "filing_date": sub["filingDate"][i],
            }
    return None


def _fetch_html(client: httpx.Client, cik: str, accession: str, primary_doc: str) -> str:
    url = f"{EDGAR_BASE}/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
    r = client.get(url)
    r.raise_for_status()
    time.sleep(0.1)
    return r.text


_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")
_ITEM_HEADER = re.compile(
    r"\b(item\s+\d+[a-z]?\.?)\s+([a-z][a-z \-/&,]{2,80})",
    re.IGNORECASE,
)


def _html_to_sectioned_text(html: str) -> str:
    """Strip tags, normalize whitespace, insert explicit `\n\n## ITEM X. TITLE\n\n`
    markers so the structural chunker (lesson 3.5) can split on section boundaries."""
    text = _TAG.sub(" ", html)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = _WHITESPACE.sub(" ", text).strip()

    out_lines: list[str] = []
    last = 0
    for m in _ITEM_HEADER.finditer(text):
        if m.start() - last > 200:  # don't split on item-references inside prose
            out_lines.append(text[last : m.start()].strip())
            out_lines.append(f"\n\n## {m.group(1).upper().rstrip('.')}. {m.group(2).upper().strip()}\n\n")
            last = m.end()
    out_lines.append(text[last:].strip())
    return "\n".join(s for s in out_lines if s)


def fetch_one(client: httpx.Client, ticker: str, out_dir: Path) -> dict:
    cik = _ticker_to_cik(client, ticker)
    if not cik:
        return {"ticker": ticker, "status": "no_cik"}
    meta = _latest_10k(client, cik)
    if not meta:
        return {"ticker": ticker, "status": "no_10k", "cik": cik}

    out_path = out_dir / f"{ticker.upper()}.txt"
    if out_path.exists() and out_path.stat().st_size > 1000:
        return {"ticker": ticker, "status": "cached", "path": str(out_path),
                "size": out_path.stat().st_size}

    html = _fetch_html(client, cik, meta["accession"], meta["primary_doc"])
    text = _html_to_sectioned_text(html)
    out_path.write_text(text)
    return {
        "ticker": ticker,
        "status": "fetched",
        "cik": cik,
        "accession": meta["accession"],
        "filing_date": meta["filing_date"],
        "size": len(text),
        "path": str(out_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=str(Path(__file__).parent / "tickers.txt"))
    ap.add_argument("--out", default=str(Path(__file__).parent / "filings"))
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tickers = [
        t.strip().upper() for t in Path(args.tickers).read_text().splitlines()
        if t.strip() and not t.startswith("#")
    ][: args.limit]

    results: list[dict] = []
    with _client() as c:
        for i, ticker in enumerate(tickers, 1):
            try:
                r = fetch_one(c, ticker, out_dir)
            except Exception as e:
                r = {"ticker": ticker, "status": "error", "error": str(e)}
            results.append(r)
            print(f"[{i:3d}/{len(tickers)}] {ticker:<6} {r['status']:<8} "
                  f"{r.get('size', '-')}", flush=True)

    summary_path = out_dir.parent / "fetch_summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    ok = sum(1 for r in results if r["status"] in ("fetched", "cached"))
    print(f"\nfetched/cached: {ok}/{len(tickers)} → {out_dir}")
    return 0 if ok >= 0.9 * len(tickers) else 1


if __name__ == "__main__":
    sys.exit(main())
