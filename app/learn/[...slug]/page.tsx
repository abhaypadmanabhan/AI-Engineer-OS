import Link from "next/link";
import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import { ChevronLeft, ChevronRight, Clock, DollarSign } from "lucide-react";
import { getAllLessons, getLessonBySlug, groupByLayer } from "@/lib/content";
import { mdxComponents } from "@/components/mdx/MDXComponents";
import { ProgressBar } from "@/components/ProgressBar";
import { CompleteButton } from "@/components/CompleteButton";

export function generateStaticParams() {
  return getAllLessons().map((l) => ({ slug: l.slug }));
}

export default function LessonPage({ params }: { params: { slug: string[] } }) {
  const lesson = getLessonBySlug(params.slug);
  if (!lesson) notFound();

  const { meta, source } = lesson;
  const groups = groupByLayer();
  const flat = groups.flatMap((g) => g.lessons);
  const idx = flat.findIndex((l) => l.slug.join("/") === params.slug.join("/"));
  const prev = idx > 0 ? flat[idx - 1] : null;
  const next = idx < flat.length - 1 ? flat[idx + 1] : null;

  const layerGroup = groups.find((g) => g.layer === meta.frontmatter.layer)!;
  const layerIndex = layerGroup.lessons.findIndex(
    (l) => l.slug.join("/") === params.slug.join("/")
  ) + 1;

  return (
    <>
      <ProgressBar
        lessons={flat.map((l) => ({ slug: l.slug, layer: l.frontmatter.layer }))}
        current={{
          slug: params.slug,
          layer: meta.frontmatter.layer,
          order: meta.frontmatter.order,
          layerTotal: layerGroup.lessons.length,
          layerIndex,
        }}
      />
      <article className="prose-lesson mx-auto px-6 py-10">
        <div className="mb-3 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="rounded bg-muted px-2 py-0.5 font-mono">
            L{meta.frontmatter.layer} · {String(meta.frontmatter.order).padStart(2, "0")}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" /> {meta.frontmatter.minutes} min
          </span>
          <span className="inline-flex items-center gap-1">
            <DollarSign className="h-3 w-3" /> ${meta.frontmatter.cost_usd.toFixed(2)} lab cost
          </span>
          {meta.frontmatter.stack.length > 0 && (
            <span className="font-mono">{meta.frontmatter.stack.join(" · ")}</span>
          )}
        </div>
        <h1>{meta.frontmatter.title}</h1>
        <MDXRemote source={source} components={mdxComponents} />

        {meta.frontmatter.interview_qs.length > 0 && (
          <section className="mt-10">
            <h2 className="font-serif">Interview questions</h2>
            {meta.frontmatter.interview_qs.map((iq, i) => (
              <mdxComponents.InterviewCard
                key={i}
                q={iq.q}
                a={iq.answer}
                difficulty={iq.difficulty}
              />
            ))}
          </section>
        )}

        <div className="mt-8 flex items-center justify-between border-t border-border pt-6">
          <CompleteButton slug={params.slug} />
          <div className="flex items-center gap-2">
            {prev && (
              <Link
                href={"/learn/" + prev.slug.join("/")}
                className="inline-flex items-center gap-1 rounded border border-border px-3 py-1.5 text-sm hover:border-accent"
              >
                <ChevronLeft className="h-4 w-4" /> {prev.frontmatter.title}
              </Link>
            )}
            {next && (
              <Link
                href={"/learn/" + next.slug.join("/")}
                className="inline-flex items-center gap-1 rounded border border-border px-3 py-1.5 text-sm hover:border-accent"
              >
                {next.frontmatter.title} <ChevronRight className="h-4 w-4" />
              </Link>
            )}
          </div>
        </div>
      </article>
    </>
  );
}
