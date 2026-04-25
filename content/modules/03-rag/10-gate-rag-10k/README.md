# L3 Mastery Gate — RAG over SEC 10-K filings

Status: **scaffold landed; reference run pending.**

The 100-filing proxy run will be appended to this README once it lands at:
`data/proxy_run_results.json`. The 500-filing reference run is gated on user
authorization after proxy results are reviewed.

## What this lesson is

Every prior L3 lesson, composed into one pipeline:

| Layer | Component | Source |
|---|---|---|
| Data | latest 10-K per ticker | `data/fetch_filings.py` (EDGAR) |
| Chunking | structural (Item X. markers) + jittered fallback | `solution.py:chunk_filing` (3.5 pattern) |
| Retrieval | hybrid BM25+embed-english-v3.0+RRF | `solution.py:hybrid_topk` (3.6 pattern) |
| Rerank | Cohere rerank-v3.5 if key, else bge-reranker-v2-m3 | `solution.py:rerank_topk` (3.6 pattern) |
| Query transforms | HyDE for multi-hop, step-back for comparison, baseline for factual | `solution.py:_route` (3.7 pattern) |
| Generation | Sonnet 4.6 with strict "answer-from-context-or-refuse" prompt | `solution.py:generate` |
| Evaluation | ragas evaluate() — unchanged signature | imported from `08-ragas/solution.py` (3.8) |

## Eval set

50 questions in `data/eval_questions.json`:

- **20 factual** — single-hop point lookups (revenue, auditor, capex, segment)
- **20 multi-hop** — synthesis across sections within one filing
- **10 comparison** — across two filings or two fiscal years

Authoring principle (per gate-design hygiene): questions written **before** the
pipeline ran on the corpus, from general 10-K domain knowledge. Some may be
unanswerable from any individual filing; the system must refuse rather than
confabulate. Context_recall is what surfaces those.

Ground-truth answers were written from public knowledge as of the model cutoff;
divergences from filing specifics will surface as context_recall variance, not
silent miscalibration.

## Two-seed proxy

`eval.py` runs the pipeline twice with seeds (7, 42). Seed controls:

- Chunk-boundary jitter (±100 chars on the structural chunker's secondary split point)
- Order of (BM25, dense) ranking lists into RRF (RRF is order-invariant in fusion
  but tie-break paths through `np.argsort` differ by float-precision noise)

Seed does NOT control LLM determinism. Sonnet at temp=0 has ~1% server-side
variance the two-seed run inevitably mixes in. That residual is real production
variance, exposed by design.

## Running

```bash
# 1. Fetch filings (one-time; idempotent caching).
python data/fetch_filings.py --limit 100

# 2. Run the eval. Writes data/proxy_run_results.json + asserts thresholds.
python eval.py
```

## Thresholds

```
faithfulness      mean(seed 7, seed 42) >= 0.85
context_precision mean(seed 7, seed 42) >= 0.75
```

If both pass, exit 0. If either fails, exit 1 with full per-seed breakdown so
you can see which component (retrieval, generation, judge) regressed.

## Scaling to 500

Same script, larger ticker list. Estimated cost based on the 100-filing proxy
will be appended here after the proxy run completes.

## Files

```
10-gate-rag-10k/
├── index.mdx                       # lesson
├── lab.ipynb                       # Colab walkthrough
├── solution.py                     # pipeline (chunking + retrieval + transforms + gen)
├── eval.py                         # two-seed harness, mean ± stdev, threshold asserts
├── README.md                       # this file
└── data/
    ├── eval_questions.json         # 50 hand-written Qs + ground truth
    ├── tickers.txt                 # S&P 100 ticker list
    ├── fetch_filings.py            # EDGAR downloader, polite rate limiting
    ├── filings/<TICKER>.txt        # extracted plain text with section markers
    └── proxy_run_results.json      # written by eval.py
```
