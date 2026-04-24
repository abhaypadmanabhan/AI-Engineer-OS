# FilingSage M1 — Structured 10-K Summarizer

Mission: pull the latest 10-K for a ticker from SEC EDGAR and emit a schema-validated summary via Anthropic `tool_use` + Pydantic.

## Install

```bash
uv sync
```

## Run

```bash
ANTHROPIC_API_KEY=sk-ant-... uv run python main.py --ticker AAPL
ANTHROPIC_API_KEY=sk-ant-... uv run python main.py --all
```

## Auto-grader

```bash
uv run python eval.py                 # uses sample_output.json
uv run python eval.py --live --ticker AAPL   # hits live APIs
```

## Cost estimate

Pricing: Claude Sonnet 4.6 = $3 / 1M input tokens, $15 / 1M output tokens.

Assume the truncated excerpt (Item 1A + Item 7) is ~40k input tokens, and the
tool_use output is ~1.5k tokens.

```
input  = (40000 / 1e6) * $3  = $0.120
output = (1500  / 1e6) * $15 = $0.0225
per ticker ≈ $0.14
5 tickers  ≈ $0.70 per full run
```

Budget well under the $0.05/query capstone target — that target is for the M6
end-to-end query loop with caching + retrieval, not this bulk-summarize step.

## SEC User-Agent note

SEC EDGAR requires a descriptive `User-Agent` with a real contact email or
they will rate-limit / block. `fetch_filings.py` sets:

```
User-Agent: FilingSage research@example.com
```

**Replace `research@example.com` with your own address before running.** See
https://www.sec.gov/os/accessing-edgar-data.

## Known limitations

- **Section truncation**: we keep only Item 1A (Risk Factors) and Item 7 (MD&A),
  capped at 150k characters. Full 10-Ks routinely exceed 500k tokens and do not
  fit Sonnet 4.6's 200k context window economically. M2 removes this limit via
  RAG over the full corpus.
- **No cross-year comparison**: the `material_changes_vs_prior_year` field is
  populated from whatever delta-language the model finds within a single
  filing. True YoY diffs arrive in M3.
- **Crude HTML stripping**: regex, not a parser. Some boilerplate leaks through.
  M2 swaps this for a real SEC XBRL-aware extractor.
- **Segment numbers may be null** when Item 7 doesn't restate them; the schema
  accepts this rather than forcing the model to fabricate.

## Forward pointer

M2 will extend this with RAG over the full filing corpus.
