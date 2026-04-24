import Link from "next/link";
import { ArrowRight, Terminal, Target, Briefcase } from "lucide-react";
import { groupByLayer } from "@/lib/content";

export default function Home() {
  const groups = groupByLayer();
  const totalLessons = groups.reduce((n, g) => n + g.lessons.length, 0);

  return (
    <main className="mx-auto max-w-5xl px-6 py-20">
      <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
        <span className="h-1.5 w-1.5 rounded-full bg-accent" />
        Code-first. Failure-driven. Job-coupled.
      </div>
      <h1 className="max-w-3xl font-serif text-5xl font-semibold leading-[1.05] tracking-tight md:text-6xl">
        Rusty Python dev → <span className="text-accent">top 0.1% AI engineer</span> in 90 days.
      </h1>
      <p className="mt-5 max-w-2xl text-lg text-muted-foreground">
        Seven layers, {totalLessons || "40+"} runnable lessons, one deployable capstone.
        No motivation fluff. No toy datasets. Every lab ships with real APIs,
        real SEC filings, and a measurable mastery gate.
      </p>

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Link
          href="/learn"
          className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 font-medium text-accent-foreground"
        >
          Start Day 1 <ArrowRight className="h-4 w-4" />
        </Link>
        <Link
          href="/capstone"
          className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 font-medium hover:border-accent"
        >
          See the capstone
        </Link>
      </div>

      <div className="mt-16 grid gap-4 md:grid-cols-3">
        <Pillar
          Icon={Terminal}
          title="Code before prose"
          body="Every concept opens with a runnable snippet in ≤30 lines. Prose comes after."
        />
        <Pillar
          Icon={Target}
          title="Mastery gates"
          body="Each module ends with a numeric threshold — recall@5, faithfulness, p95 latency. Vibes don't pass."
        />
        <Pillar
          Icon={Briefcase}
          title="Interview-coupled"
          body="Every lesson ships with 3 real interview questions and expected answers, tagged by difficulty."
        />
      </div>

      <section className="mt-20">
        <div className="mb-4 text-xs font-semibold uppercase tracking-wide text-accent">
          The path
        </div>
        <div className="grid gap-2">
          {groups.map((g) => (
            <Link
              key={g.layerSlug}
              href={g.lessons[0] ? "/learn/" + g.lessons[0].slug.join("/") : "/learn"}
              className="flex items-center gap-4 rounded-md border border-border bg-card px-4 py-3 hover:border-accent"
            >
              <span className="font-mono text-xs text-muted-foreground">L{g.layer}</span>
              <span className="font-serif text-lg">{g.title}</span>
              <span className="ml-auto text-xs text-muted-foreground">
                {g.lessons.length} lessons
              </span>
            </Link>
          ))}
          {groups.length === 0 && (
            <div className="rounded-md border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              Content not built yet. Placeholder lesson coming next.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function Pillar({ Icon, title, body }: { Icon: any; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <Icon className="h-5 w-5 text-accent" />
      <div className="mt-3 font-serif text-lg">{title}</div>
      <p className="mt-1 text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
