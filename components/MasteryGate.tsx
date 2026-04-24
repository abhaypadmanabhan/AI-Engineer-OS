"use client";
import { useEffect, useState } from "react";
import { Check, Target } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  metric: string;
  threshold: number;
  slug?: string;   // unique key for localStorage
  children?: React.ReactNode;
};

export function MasteryGate({ metric, threshold, slug, children }: Props) {
  const key = `gate:${slug ?? metric}`;
  const [value, setValue] = useState<string>("");
  const [passed, setPassed] = useState(false);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(key) : null;
    if (stored === "1") setPassed(true);
  }, [key]);

  function check() {
    const n = parseFloat(value);
    if (Number.isFinite(n) && n >= threshold) {
      setPassed(true);
      localStorage.setItem(key, "1");
    } else {
      setPassed(false);
      localStorage.removeItem(key);
    }
  }

  return (
    <div
      className={cn(
        "my-8 rounded-lg border p-5",
        passed
          ? "border-accent/60 bg-accent/5"
          : "border-border bg-card"
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        {passed ? (
          <Check className="h-5 w-5 text-accent" />
        ) : (
          <Target className="h-5 w-5 text-accent" />
        )}
        <span className="font-serif text-lg">
          Mastery Gate: <span className="font-mono text-sm">{metric} ≥ {threshold}</span>
        </span>
      </div>
      {children && <div className="mb-3 text-sm text-muted-foreground">{children}</div>}
      <div className="flex items-center gap-2">
        <input
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={`your ${metric}`}
          className="w-48 rounded border border-border bg-background px-2 py-1 font-mono text-sm outline-none focus:border-accent"
        />
        <button
          onClick={check}
          className="rounded bg-accent px-3 py-1 text-sm font-medium text-accent-foreground hover:opacity-90"
        >
          Verify
        </button>
        {passed && (
          <span className="text-sm font-medium text-accent">
            Passed. Saved locally.
          </span>
        )}
      </div>
    </div>
  );
}
