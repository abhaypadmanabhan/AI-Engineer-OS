"""SEC EDGAR fetcher for the latest 10-K per ticker.

SEC requires a descriptive User-Agent with a real contact email. Replace
`research@example.com` with your own before running. See:
https://www.sec.gov/os/accessing-edgar-data

Flow:
    1. Resolve ticker -> CIK via company_tickers.json (cached).
    2. Hit /submissions/CIK{cik}.json to list recent filings.
    3. Pick the most recent 10-K, download the primary document.
    4. Cache raw text at cache/{ticker}_{accession}.txt.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx

SEC_UA = "FilingSage research@example.com"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}/{doc}"


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"},
        timeout=30.0,
        follow_redirects=True,
    )


def load_ticker_map(client: httpx.Client) -> dict[str, str]:
    """Return {TICKER: zero-padded 10-digit CIK}."""
    cache_path = CACHE_DIR / "company_tickers.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
    else:
        resp = client.get(TICKERS_URL)
        resp.raise_for_status()
        data = resp.json()
        cache_path.write_text(json.dumps(data))
    out: dict[str, str] = {}
    for row in data.values():
        out[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
    return out


def get_latest_10k(ticker: str) -> tuple[str, str, str]:
    """Return (accession_number, primary_document_name, fiscal_year_end_iso)."""
    with _client() as client:
        tmap = load_ticker_map(client)
        ticker = ticker.upper()
        if ticker not in tmap:
            raise ValueError(f"Unknown ticker: {ticker}")
        cik = tmap[ticker]
        sub = client.get(SUBMISSIONS_URL.format(cik=cik))
        sub.raise_for_status()
        filings = sub.json()["filings"]["recent"]
        forms = filings["form"]
        for i, form in enumerate(forms):
            if form == "10-K":
                return (
                    filings["accessionNumber"][i],
                    filings["primaryDocument"][i],
                    filings["reportDate"][i],
                )
    raise RuntimeError(f"No 10-K found for {ticker}")


def fetch_10k_text(ticker: str) -> tuple[str, str, str]:
    """Fetch + cache the latest 10-K primary doc text.

    Returns (accession_number, fiscal_year_end_iso, text).
    """
    with _client() as client:
        tmap = load_ticker_map(client)
        cik = tmap[ticker.upper()]
    accession, doc, fy_end = get_latest_10k(ticker)

    cache_path = CACHE_DIR / f"{ticker.upper()}_{accession}.txt"
    if cache_path.exists():
        return accession, fy_end, cache_path.read_text()

    with _client() as client:
        url = ARCHIVES_URL.format(
            cik_int=int(cik),
            accession_nodash=accession.replace("-", ""),
            doc=doc,
        )
        resp = client.get(url)
        resp.raise_for_status()
        html = resp.text
    # Crude HTML -> text. Good enough for M1; M2 will use a real parser.
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    cache_path.write_text(text)
    return accession, fy_end, text


def extract_sections(text: str, max_chars: int = 150_000) -> str:
    """Try to slice out Item 1A (Risk Factors) and Item 7 (MD&A).

    Falls back to the first `max_chars` characters if markers are absent.
    10-Ks routinely exceed 500k tokens of full text; Claude Sonnet 4.6's
    200k context can't take the whole thing economically anyway.
    """
    lower = text.lower()
    i1a = lower.find("item 1a")
    i7 = lower.find("item 7.")
    i8 = lower.find("item 8.")

    chunks: list[str] = []
    if i1a != -1:
        end = text.find("Item 1B", i1a) if text.find("Item 1B", i1a) != -1 else i1a + 60_000
        chunks.append(text[i1a:end])
    if i7 != -1 and i8 != -1:
        chunks.append(text[i7:i8])

    if chunks:
        joined = "\n\n---\n\n".join(chunks)
        return joined[:max_chars]
    return text[:max_chars]


if __name__ == "__main__":
    import sys

    t = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    accession, fy_end, body = fetch_10k_text(t)
    sliced = extract_sections(body)
    print(f"{t} accession={accession} fy_end={fy_end} chars={len(sliced)}")
