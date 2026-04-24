# AI Engineer OS

Interactive learning platform that takes a rusty Python developer to a hireable AI engineer in 60–90 days. Code-first, failure-driven, job-coupled.

## What this is

- **7-layer curriculum** (Setup → Foundations → LLM primitives → RAG → Agents + MCP → Production → Advanced → Top 0.1%)
- **One capstone:** **FilingSage** — multi-agent RAG over SEC filings, deployed end-to-end
- **Each lesson:** runnable lab, cost + latency tag, numeric mastery gate, 3 interview Qs

Not a tutorial site. A production-grade web app whose content *is* the curriculum.

## Quickstart (≤5 minutes)

```bash
git clone <this-repo> && cd ai-engineer-os
npm install
npm run dev          # http://localhost:3000 (or 3001 if occupied)
```

Visit `/learn/00-setup/01-toolchain` to see a rendered lesson.

## Repo layout

```
app/                 Next.js App Router
  learn/[...slug]/   dynamic lesson renderer (MDX)
  capstone/          FilingSage overview page
components/          CodeBlock, MasteryGate, CostMeter, Sidebar, ProgressBar, DiagramMermaid, InterviewCard, Callout
content/modules/     MDX lessons. One folder per lesson.
  <LL>-<slug>/<NN>-<slug>/
    index.mdx        the lesson
    lab.ipynb        Colab-ready notebook (added per layer)
    solution.py      reference solution
    eval.py          local auto-grader
lib/                 content loader, shiki, schema (zod), colab URL helper
capstone/filingsage/ the capstone repo (added after L5)
SPEC.md              full curriculum index + mastery rubrics
CLAUDE.md            pedagogy conventions for future contributors / AI agents
```

## Writing lessons

See `CLAUDE.md` for conventions. Minimum contract:

- Code block within the first 3 sentences
- ≥40% of the body is code
- ≤800 words of prose
- Ends with a `<MasteryGate metric="..." threshold={...} />` and exactly 3 interview Qs in frontmatter

Frontmatter is zod-validated (`lib/schema.ts`). Bad frontmatter → the lesson is skipped at build time with a console warning.

## Deploy

```bash
vercel deploy --prod
```

Set `NEXT_PUBLIC_GH_USER` / `NEXT_PUBLIC_GH_REPO` / `NEXT_PUBLIC_GH_BRANCH` so the "Open in Colab" buttons point to your fork.

## Status

- [x] Phase 1 — scaffold + components + MDX pipeline
- [x] Phase 2 — curriculum content (L0 complete, L1/L2/L3 started)
- [ ] Phase 3 — FilingSage capstone
- [ ] Phase 4 — Vercel deploy + Lighthouse ≥95
