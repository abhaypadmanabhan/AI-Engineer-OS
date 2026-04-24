# FilingSage

Autonomous multi-agent research over SEC 10-K/10-Q filings, earnings calls, and news. Produces cited research briefs on public tickers at <$0.05/query with Ragas faithfulness >0.85.

## Mission
Ship a production-grade financial research agent that a junior analyst would trust. Every claim is cited back to filing section + paragraph. No hallucinations silently pass the faithfulness gate.

## Milestones

| Milestone | Layer | Scope | Status |
|-----------|-------|-------|--------|
| M1 — Summarizer | L2 | Structured 10-K summary via `tool_use` + Pydantic | Shipped |
| M2 — RAG | L3 | Chunk + embed full filing corpus; retrieval QA | Pending |
| M3 — Cross-year | L3 | Diff across 3 years of 10-K/10-Q | Pending |
| M4 — Multi-source | L4 | Add earnings-call transcripts + news | Pending |
| M5 — Agent orchestration | L5 | LangGraph planner + tool-executor + critic | Pending |
| M6 — Evals + Ragas gate | L6 | Faithfulness >0.85, cost <$0.05/query, latency p95 <12s | Pending |

## Current status
M1 shipped in `m1-summarizer/`. M2+ pending.

## Cost target
End-to-end query budget: $0.05. Tracked via `<CostMeter>` on every lesson that ships a FilingSage component.
