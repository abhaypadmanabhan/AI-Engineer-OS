import { CostMeter } from "@/components/CostMeter";

export default function CapstonePage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-accent">
        Capstone
      </div>
      <h1 className="font-serif text-4xl font-semibold">FilingSage</h1>
      <p className="mt-3 text-lg text-muted-foreground">
        Autonomous multi-agent system over SEC 10-K/10-Q, earnings-call transcripts,
        and financial news. Produces cited research briefs on any public ticker with
        strict faithfulness evals.
      </p>

      <CostMeter cost="$0.04" latency="22s" tokens="18k" />

      <h2 className="mt-10 font-serif text-2xl">Milestones</h2>
      <ol className="mt-4 space-y-3">
        {MILESTONES.map((m) => (
          <li key={m.id} className="rounded-md border border-border bg-card p-4">
            <div className="flex items-baseline gap-3">
              <span className="font-mono text-xs text-accent">{m.id}</span>
              <span className="font-serif text-lg">{m.title}</span>
              <span className="ml-auto text-xs text-muted-foreground">after {m.after}</span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{m.detail}</p>
          </li>
        ))}
      </ol>
    </main>
  );
}

const MILESTONES = [
  { id: "M1", after: "L2", title: "Filing summarizer", detail: "Pull latest 10-K for 5 tickers, produce one-page summary with tool-call structure." },
  { id: "M2", after: "L3", title: "RAG over 500 filings", detail: "Qdrant index, hybrid search + rerank. Ragas faithfulness ≥ 0.85 on 50-question eval set." },
  { id: "M3", after: "L4", title: "3-agent crew + MCP", detail: "Fetcher · Analyst · Writer. EDGAR, yfinance, news exposed via MCP tools." },
  { id: "M4", after: "L5", title: "Production deploy", detail: "Modal + Vercel, Langfuse traces, p95 < 2.5s, < $0.01 per query, full guardrails." },
  { id: "M5", after: "L6", title: "LoRA relevance classifier", detail: "Fine-tuned 8B replaces the relevance LLM. 100× cost cut, ≥98% of LLM quality." },
  { id: "M6", after: "L7", title: "Portfolio package", detail: "System design writeup, 90-second demo video, recruiter-ready README." },
];
