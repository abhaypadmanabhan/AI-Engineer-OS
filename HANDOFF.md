# Session Handoff — Phase 1 → Phase 2

## Where we are
Phase 1 complete. Next.js 14 learning platform scaffold builds clean, 14 pages SSG, 7 seed lessons render end-to-end across L0–L3.

**Read first:** `SPEC.md` (curriculum + mastery rubrics), `CLAUDE.md` (pedagogy conventions, non-negotiable rules), `README.md`.

## Locked decisions
- Host: Vercel
- Default LLM: Anthropic Claude Sonnet 4.6; GPT-5 for contrast
- Tooling: hybrid OSS-default (Qdrant local, Langfuse self-host, Voyage free tier)
- Python baseline: 3–4/10 → L1 gets full 6-day depth
- Capstone: **FilingSage** (SEC 10-K/Q + earnings + news, cited briefs, Ragas faithfulness ≥0.85)

## What exists
```
app/                (marketing) + /learn + /learn/[...slug] + /capstone
components/         CodeBlock, CostMeter, MasteryGate, InterviewCard,
                    DiagramMermaid, Callout, Sidebar, ProgressBar,
                    CompleteButton, mdx/{PreCode,MDXComponents}
lib/                content.ts, schema.ts (zod FM), shiki.ts, colab.ts, utils.ts
content/modules/
  00-setup/         01-toolchain, 02-api-keys, 03-first-call, 04-git-for-ai  (4/4)
  01-foundations/   01-modern-python                                          (1/6)
  02-llm-primitives/04-structured-outputs                                     (1/8)
  03-rag/           03-naive-rag                                              (1/10)
SPEC.md, CLAUDE.md, README.md, HANDOFF.md
tailwind.config.ts  dark-default, Fraunces/Plex/JetBrains Mono, accent token
```

## Verified
- `npm run build` clean
- Dev server: `/`, `/learn`, `/learn/00-setup/01-toolchain`, `/learn/03-rag/03-naive-rag`, `/capstone` → 200
- MDX frontmatter zod-validated; invalid files auto-skipped with console warn

## Debt / known gaps (fix in Phase 2)
1. **UI built by hand, not via shadcn MCP.** Replace ad-hoc buttons/cards with shadcn primitives (`Button`, `Card`, `Tabs`, `Dialog`, `Sheet`, `ScrollArea`, `Tooltip`). Use `shadcn` MCP + `frontend-design` skill together.
2. No mobile drawer for sidebar — desktop only. Add a `Sheet` trigger.
3. `DiagramMermaid` not yet exercised in any lesson.
4. No `/playground` route (Pyodide or BYOK Anthropic proxy) — planned L2.
5. Colab links point to `your-handle/ai-engineer-os` placeholder. Set `NEXT_PUBLIC_GH_USER/REPO/BRANCH` when the repo is pushed.
6. No tests. No Lighthouse run yet.
7. Content: 7 of ~54 target lessons written (~13%).
8. Capstone dir `capstone/filingsage/` not yet created.

## Conventions (enforce ruthlessly; see CLAUDE.md)
- Code inside first 3 sentences of every lesson
- ≥40% lines are code, ≤800 prose words
- Every lab has `<CostMeter>` with computed (not guessed) cost
- Every lesson ends with `<MasteryGate metric=... threshold={N} slug="<layer>/<lesson>">` + exactly 3 `interview_qs` in frontmatter
- "Watch it break" block required for every framework lesson
- Raw SDKs default; LlamaIndex for retrieval only; LangGraph for orchestration only; no LangChain without justification

## Phase 2 scope (what next session owns)
1. **UI polish pass** using shadcn MCP + frontend-design skill. Replace hand-rolled components. Add mobile Sheet sidebar. Ship `/playground` with BYOK Anthropic streaming.
2. **Finish Layer 0** (already done — verify) and **Layer 1** (5 more lessons: 02 httpx, 03 pydantic, 04 pandas-minimum, 05 debugging, 06 gate-HN-CLI).
3. **Complete Layer 2** (7 more lessons) + **Capstone M1**: `capstone/filingsage/` skeleton with 10-K summarizer.
4. Per-lesson: write `lab.ipynb`, `solution.py`, `eval.py` alongside `index.mdx`.
5. Report at each layer boundary: #lessons, code%, word count, cost to run labs, sample screenshot URL.

## Runbook for next session
```bash
cd /Users/abhayp/Downloads/Projects/AI_Engineer/ai-engineer-os
npm run dev          # sanity check
npm run build        # must stay green
```
