import Link from "next/link";
import { groupByLayer } from "@/lib/content";

export default function LearnIndex() {
  const groups = groupByLayer();
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="font-serif text-4xl font-semibold">Curriculum</h1>
      <p className="mt-3 text-muted-foreground">
        Seven layers. ~90 days. Every lesson ends with a measurable mastery gate.
      </p>
      <div className="mt-8 space-y-8">
        {groups.map((g) => (
          <section key={g.layerSlug}>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-accent">
              Layer {g.layer}
            </div>
            <h2 className="font-serif text-2xl">{g.title}</h2>
            <ul className="mt-3 divide-y divide-border border-y border-border">
              {g.lessons.map((l) => (
                <li key={l.slug.join("/")}>
                  <Link
                    href={"/learn/" + l.slug.join("/")}
                    className="flex items-baseline gap-3 py-2 text-sm hover:text-accent"
                  >
                    <span className="font-mono text-xs text-muted-foreground">
                      {String(l.frontmatter.order).padStart(2, "0")}
                    </span>
                    <span className="flex-1">{l.frontmatter.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {l.frontmatter.minutes}m · ${l.frontmatter.cost_usd.toFixed(2)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
