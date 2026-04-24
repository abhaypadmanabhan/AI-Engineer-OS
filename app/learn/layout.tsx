import { Sidebar } from "@/components/Sidebar";
import { groupByLayer } from "@/lib/content";

export default function LearnLayout({ children }: { children: React.ReactNode }) {
  const groups = groupByLayer().map((g) => ({
    layerSlug: g.layerSlug,
    layer: g.layer,
    title: g.title,
    lessons: g.lessons.map((l) => ({
      slug: l.slug,
      title: l.frontmatter.title,
      minutes: l.frontmatter.minutes,
      order: l.frontmatter.order,
    })),
  }));

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-border md:block">
        <Sidebar groups={groups} />
      </aside>
      <main className="flex-1">{children}</main>
    </div>
  );
}
