# CLAUDE.md — AI Engineer OS Conventions

## Product
Interactive learning site. Not a doc. Code-first pedagogy. Every lesson must be runnable, cited, cost-tagged.

## Non-negotiable pedagogy rules
1. **Code within first 3 sentences.** No preambles. No "in this module".
2. **≥40% lines are code** (measured on `index.mdx`).
3. **≤800 prose words** per lesson.
4. Every lab has `<CostMeter cost="$0.04" latency="1.8s" />` block.
5. Every module ends with `<MasteryGate>` (numeric threshold) + exactly 3 `<InterviewCard>`.
6. **No motivation filler.** No AI history. No "AI is changing the world."
7. **Failure-driven:** every lesson with a framework shows it breaking first, then fix.
8. **From-scratch before framework:** naive RAG before LlamaIndex; ReAct before LangGraph.
9. **Real data only:** arXiv papers, SEC filings, GitHub READMEs. No Lorem Ipsum, no toy MNIST.
10. Frameworks: raw SDKs default, LlamaIndex for retrieval only, LangGraph for orchestration only. **No LangChain without justification.**

## MDX frontmatter (zod enforced)
```yaml
---
title: "Naive RAG in 50 lines"
layer: 3
order: 3
minutes: 35
cost_usd: 0.08
p95_latency_ms: 2400
stack: ["anthropic", "qdrant", "voyage"]
gate:
  metric: "recall_at_5"
  threshold: 0.6
interview_qs:
  - q: "Why does cosine similarity fail on long documents?"
    answer: "Averaging dilutes signal. Chunk + aggregate via maxsim or rerank."
    difficulty: "mid"
---
```

## File layout per lesson
```
content/modules/<LL>-<slug>/<NN>-<slug>/
  index.mdx      # lesson
  lab.ipynb      # Colab-ready
  solution.py    # reference
  eval.py        # auto-grader
  data/          # real dataset (gitignore if >10MB, provide download script)
```

## Component usage
- `<CodeBlock lang="python" colabPath="03-rag/03-naive/lab.ipynb">...</CodeBlock>` — auto-adds copy + Colab button
- `<CostMeter cost="$0.08" latency="2.4s" tokens="12k" />`
- `<DiagramMermaid>graph LR; A-->B;</DiagramMermaid>`
- `<MasteryGate metric="recall_at_5" threshold={0.6} />`
- `<InterviewCard difficulty="mid" q="..." a="..." />`

## Writing style
- Imperative. "Run this." not "You can run this."
- No emoji unless user asks. No "🎉 Congrats!" celebratory blocks.
- No bullet-point summaries at lesson end. The MasteryGate is the summary.
- Show `$ pip install ...` but prefer `uv add ...` as the taught way.

## LLM API defaults in code
- Default model: `claude-sonnet-4-6`
- Contrast example: `gpt-5`
- Always show: `max_tokens`, `temperature=0` for deterministic examples
- Always wrap keys: `os.environ["ANTHROPIC_API_KEY"]`, never hardcoded

## Cost discipline
- Every lab estimated cost must be computed, not guessed. Use: `(input_tokens * $/1M_in) + (output_tokens * $/1M_out)`.
- If lab >$0.50, add `<Warning>` block and offer a scaled-down variant.

## When in doubt
Re-read `SPEC.md`. If still in doubt, show code, not prose.
