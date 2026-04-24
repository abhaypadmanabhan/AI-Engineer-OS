"use client";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  q: string;
  a: string;
  difficulty?: "junior" | "mid" | "senior";
};

const tone = {
  junior: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  mid: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  senior: "bg-rose-500/10 text-rose-400 border-rose-500/30",
};

export function InterviewCard({ q, a, difficulty = "mid" }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <div className="my-3 rounded-lg border border-border bg-card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start gap-3 p-4 text-left"
      >
        <span
          className={cn(
            "mt-0.5 rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide",
            tone[difficulty]
          )}
        >
          {difficulty}
        </span>
        <span className="flex-1 text-sm">{q}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </button>
      {open && (
        <div className="border-t border-border px-4 pb-4 pt-3 text-sm text-muted-foreground">
          <div className="mb-1 text-xs uppercase tracking-wide text-accent">
            Expected answer
          </div>
          {a}
        </div>
      )}
    </div>
  );
}
