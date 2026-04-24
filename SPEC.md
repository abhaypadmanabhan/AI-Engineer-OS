# AI Engineer OS — SPEC

Interactive learning platform + curriculum + deployable capstone. Takes rusty Python dev → top 0.1% AI Engineer hireable at Bay Area startups in 60-90 days.

## Locked decisions
| Axis | Choice |
|---|---|
| Host | Vercel |
| Default LLM | Anthropic Claude Sonnet 4.6 primary, GPT-5 secondary |
| Tooling | Hybrid: OSS default (Qdrant local, Langfuse self-host, Voyage free), paid shown as prod upgrade |
| Python baseline | 3-4/10 very rusty — Layer 1 full 6-day depth |
| Capstone | **FilingSage** — agent over SEC 10-K/10-Q + earnings + news, cited briefs, strict faithfulness |
| Auth | None. localStorage progress. No DB. |

## Stack
- Next.js 14 App Router + TS + Tailwind + shadcn/ui
- `next-mdx-remote` (MDX lessons)
- `shiki` (dual-theme code highlight)
- `mermaid` (client-side diagrams)
- Fonts: Fraunces (h1), IBM Plex Sans (body), JetBrains Mono (code)
- `zod` (MDX frontmatter validation)
- Vercel deploy, optional `/api/anthropic` BYOK proxy

## Curriculum map

### L0 Setup (Day 1 · 4 lessons)
- 01 Toolchain (uv, ruff, pyproject, direnv)
- 02 API keys (Anthropic, OpenAI, OpenRouter, HF, Modal)
- 03 First call: Sonnet 4.6 + GPT-5 + Gemini 2.5 side-by-side, measure $ + latency
- 04 Git for AI projects (.gitignore for .env, weights, vector stores)

### L1 Foundations (Days 2-7 · 6 lessons)
- 01 Modern Python: types, dataclasses, async/await, context managers
- 02 HTTP in 2026: httpx async, tenacity retries, rate limits
- 03 JSON + Pydantic v2
- 04 Pandas minimum (read_csv, groupby, merge, to_dict for LLMs)
- 05 Debug like a pro: pdb, structlog
- 06 **Gate:** HN CLI paginator → structured JSON

### L2 LLM Primitives (Days 8-14 · 8 lessons)
- 01 What an LLM is (1 diagram, move on)
- 02 Tokens, context, temp, top_p
- 03 Anthropic + OpenAI SDKs: stream, tool use, vision, batch
- 04 Structured outputs: JSON mode + tool calling + Pydantic
- 05 Prompting fundamentals: system, few-shot, XML tags, delimiters
- 06 Advanced prompting: CoT, prefilling, decomposition, self-consistency
- 07 Promptfoo versioning (yaml, git-trackable)
- 08 **Gate:** classify 200 support tickets into 12 categories >88%, 4-prompt Promptfoo matrix
- **Capstone M1:** scrape + summarize latest 10-K for 5 tickers (AAPL, MSFT, NVDA, GOOG, META)

### L3 Embeddings + RAG (Days 15-28 · 10 lessons)
- 01 Embeddings + cosine from scratch (numpy, 20 lines)
- 02 Vector DB comparison: Qdrant, Pinecone, pgvector, Chroma, Weaviate
- 03 Naive RAG in 50 lines (no framework), 100 arXiv papers, watch it fail
- 04 Failure modes: chunk boundaries, lost context, irrelevant top-k
- 05 Chunking: fixed, semantic, recursive, structural
- 06 Hybrid BM25+dense, Voyage/Cohere rerankers
- 07 Query transforms: HyDE, decomposition, step-back, multi-query
- 08 Ragas: faithfulness, relevance, context precision+recall
- 09 Introduce LlamaIndex, show what it abstracted
- 10 **Gate:** RAG over 500 SEC 10-Ks. Faithfulness >0.85, context precision >0.75 on 50-Q eval set
- **Capstone M2:** production RAG on 500 filings, citations required

### L4 Agents + MCP (Days 29-42 · 9 lessons)
- 01 ReAct in 80 lines: calculator + web search + file read
- 02 Watch it break: loops, hallucinated tools, bad args. Fix each.
- 03 Tool design: schemas, descriptions, recoverable errors
- 04 **MCP deep dive:** build FastMCP server with 3 tools, connect Claude Desktop + custom Python client
- 05 LangGraph: when state machines beat ReAct. Research agent with conditional edges.
- 06 Multi-agent: supervisor, swarm, hierarchical. 3-agent code review crew.
- 07 Memory: short-term, long-term vector, episodic log. Implement all three.
- 08 Agent eval: trajectory, tool-use precision, task completion
- 09 **Gate:** Deep Research agent, 70%+ cited claims verifiable
- **Capstone M3:** 3-agent FilingSage (fetcher, analyst, writer) with MCP tools (EDGAR, yfinance, news)

### L5 Production (Days 43-56 · 10 lessons)
- 01 FastAPI for AI: async, SSE streaming, background tasks, DI
- 02 Caching: Anthropic prompt cache, semantic cache (GPTCache), Redis for tools
- 03 Cost: model routing, prompt compression, batch API
- 04 Latency: streaming, parallel tool calls, edge deploy
- 05 **Observability:** Langfuse + OpenTelemetry, traces, spans, prod eval scores
- 06 Guardrails: injection defense, PII (Presidio), output validation, refusals
- 07 Rate limits, retries, circuit breakers, fallback chains
- 08 Deploy: Modal (AI workloads), Vercel (frontend), Railway (Postgres+Qdrant)
- 09 CI/CD: Promptfoo in GH Actions, PR regression gates
- 10 **Gate:** Layer 3 RAG + observability + caching + guardrails. p95<2.5s, <$0.01/query, Langfuse traces visible
- **Capstone M4:** FilingSage deployed Modal+Vercel, Langfuse, cost+latency targets hit

### L6 Advanced (Days 57-70 · 9 lessons)
- 01 Fine-tune: when worth it (>1k examples, narrow, cost/latency)
- 02 LoRA/QLoRA hands-on: Llama 3.3 8B with unsloth+trl on Colab T4
- 03 DSPy: optimize prompts by metric. Redo L2 prompt, measure lift.
- 04 Voice: Whisper STT + Cartesia/ElevenLabs TTS + interrupt handling, sub-second
- 05 Multimodal: Claude vision + structured PDF/screenshot extraction
- 06 Local stack: Ollama + llama.cpp + vLLM — when each wins
- 07 Realtime: OpenAI Realtime API, Anthropic streaming + tools over WS
- 08 Synthetic data for evals + FT datasets
- 09 **Gate:** pick one — (a) FT classifier beats GPT-5 at 1/100th cost, OR (b) <1.5s voice agent books meeting
- **Capstone M5:** FilingSage relevance classifier as LoRA 8B (100x cost cut vs LLM)

### L7 Top 0.1% (Days 71-90 · 8 lessons)
- 01 System design drills: ChatGPT, Perplexity, Cursor autocomplete, support copilot (1hr each, rubric)
- 02 Tradeoffs: latency vs quality vs cost, how to communicate
- 03 Failure taxonomy: silent fails, drift, prompt regression, eval leakage, judge bias
- 04 Build your own eval harness (job-winning)
- 05 Reading + shipping from research (20-min paper → technique)
- 06 Startup AI engineer job: scope, ship, demo, say "this won't work"
- 07 Resume + GitHub + portfolio polish
- 08 **Gate:** 5 recorded mock interviews, self-graded rubrics
- **Capstone M6:** system design writeup + demo video + recruiter README

## Mastery Gate schema (MDX frontmatter)
```yaml
gate:
  metric: "ticket_classification_accuracy"
  threshold: 0.88
  eval_script: "content/modules/02-llm-primitives/08-gate/eval.py"
  dataset: "content/modules/02-llm-primitives/08-gate/data/tickets.jsonl"
```
Learner pastes output → local JS validator checks threshold → localStorage marks complete.

## Lesson frontmatter contract (zod-validated)
```yaml
title: string
layer: 0-7
order: int
minutes: int
cost_usd: number  # estimated to run lab
p95_latency_ms: int | null
stack: string[]
gate?: Gate
interview_qs: [{q, answer, difficulty}]
```

## Capstone — FilingSage
**One-line:** "Autonomous multi-agent system that ingests SEC filings + earnings calls + news and produces cited research briefs on any public ticker at <$0.05/query with Ragas faithfulness >0.85."

**Milestones land per layer (M1-M6 above).**

**Repo:** `capstone/filingsage/` — own README, deploy script, eval suite, demo video script.

## Verification
- `pnpm dev` + navigate to `/learn/00-setup/01-toolchain` → syntax-highlighted code, copy button, Colab link, MasteryGate persists via localStorage
- Per layer: `pnpm build` clean, sample lesson renders, Colab link opens, `eval.py` passes on `solution.py`
- Capstone: `make run TICKER=AAPL` → cited brief in <30s, Langfuse trace, Ragas >0.85 on 50-Q set
- Final: Vercel deploy URL, Lighthouse ≥95 on lesson page, fresh clone → 5-min quickstart works
