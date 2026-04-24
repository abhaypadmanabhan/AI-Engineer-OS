"use client";
import { useEffect, useState } from "react";

type Lesson = { slug: string[]; layer: number };

export function ProgressBar({
  lessons,
  current,
}: {
  lessons: Lesson[];
  current?: { slug: string[]; layer: number; order: number; layerTotal: number; layerIndex: number };
}) {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    let done = 0;
    for (const l of lessons) {
      if (localStorage.getItem(`done:${l.slug.join("/")}`) === "1") done++;
    }
    setPct(lessons.length ? Math.round((done / lessons.length) * 100) : 0);
  }, [lessons]);

  return (
    <div className="sticky top-0 z-20 flex items-center gap-4 border-b border-border bg-background/80 px-6 py-2 text-xs backdrop-blur">
      {current && (
        <span className="text-muted-foreground">
          <span className="text-foreground">Layer {current.layer}</span> ·{" "}
          Lesson {current.layerIndex} of {current.layerTotal}
        </span>
      )}
      <div className="ml-auto flex items-center gap-2">
        <span className="text-muted-foreground">{pct}% to job-ready</span>
        <div className="h-1.5 w-32 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-accent transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
