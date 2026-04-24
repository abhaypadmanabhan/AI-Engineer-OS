"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ChevronRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

type Lesson = {
  slug: string[];
  title: string;
  minutes: number;
  order: number;
};
type Group = {
  layerSlug: string;
  layer: number;
  title: string;
  lessons: Lesson[];
};

export function Sidebar({ groups }: { groups: Group[] }) {
  const pathname = usePathname();
  const [completed, setCompleted] = useState<Record<string, boolean>>({});
  const [openLayers, setOpenLayers] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(groups.map((g) => [g.layerSlug, true]))
  );

  useEffect(() => {
    const c: Record<string, boolean> = {};
    for (const g of groups) {
      for (const l of g.lessons) {
        const k = `done:${l.slug.join("/")}`;
        if (localStorage.getItem(k) === "1") c[l.slug.join("/")] = true;
      }
    }
    setCompleted(c);
  }, [groups]);

  return (
    <nav className="scrollbar-thin h-full overflow-y-auto px-4 py-6">
      <Link href="/" className="mb-6 block">
        <div className="font-serif text-xl font-semibold">AI Engineer OS</div>
        <div className="text-xs text-muted-foreground">90-day path to hireable</div>
      </Link>

      {groups.map((g) => {
        const isOpen = openLayers[g.layerSlug];
        return (
          <div key={g.layerSlug} className="mb-3">
            <button
              onClick={() =>
                setOpenLayers((s) => ({ ...s, [g.layerSlug]: !s[g.layerSlug] }))
              }
              className="flex w-full items-center gap-2 py-1 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:text-foreground"
            >
              <ChevronRight
                className={cn("h-3 w-3 transition-transform", isOpen && "rotate-90")}
              />
              <span>L{g.layer}</span>
              <span>{g.title}</span>
            </button>
            {isOpen && (
              <ul className="ml-4 mt-1 border-l border-border">
                {g.lessons.map((l) => {
                  const href = "/learn/" + l.slug.join("/");
                  const active = pathname === href;
                  const done = completed[l.slug.join("/")];
                  return (
                    <li key={l.slug.join("/")}>
                      <Link
                        href={href}
                        className={cn(
                          "flex items-center gap-2 border-l-2 py-1.5 pl-3 -ml-[1px] text-sm transition-colors",
                          active
                            ? "border-accent text-foreground"
                            : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <span
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[10px]",
                            done
                              ? "border-accent bg-accent/20 text-accent"
                              : "border-border text-muted-foreground"
                          )}
                        >
                          {done ? <Check className="h-3 w-3" /> : l.order}
                        </span>
                        <span className="flex-1 truncate">{l.title}</span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {l.minutes}m
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        );
      })}
    </nav>
  );
}
