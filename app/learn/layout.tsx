import { Sidebar } from "@/components/Sidebar";
import { MobileSidebar } from "@/components/MobileSidebar";
import { groupByLayer } from "@/lib/content";
import Link from "next/link";

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
      <div className="flex flex-1 flex-col">
        <div className="sticky top-0 z-30 flex items-center gap-2 border-b border-border bg-background/80 px-3 py-2 backdrop-blur md:hidden">
          <MobileSidebar groups={groups} />
          <Link href="/" className="font-serif text-base font-semibold">AI Engineer OS</Link>
        </div>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
