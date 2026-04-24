"use client";
import { useEffect, useState } from "react";
import { Check, Target } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

type Props = {
  metric: string;
  threshold: number;
  slug?: string;
  children?: React.ReactNode;
};

export function MasteryGate({ metric, threshold, slug, children }: Props) {
  const key = `gate:${slug ?? metric}`;
  const [value, setValue] = useState<string>("");
  const [passed, setPassed] = useState(false);
  const [lastVal, setLastVal] = useState<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(key);
    if (stored === "1") setPassed(true);
    const v = localStorage.getItem(`${key}:val`);
    if (v) setLastVal(parseFloat(v));
  }, [key]);

  function check() {
    const n = parseFloat(value);
    if (!Number.isFinite(n)) return;
    setLastVal(n);
    localStorage.setItem(`${key}:val`, String(n));
    if (n >= threshold) {
      setPassed(true);
      localStorage.setItem(key, "1");
    } else {
      setPassed(false);
      localStorage.removeItem(key);
    }
  }

  const pct = lastVal == null ? 0 : Math.min(100, Math.round((lastVal / threshold) * 100));

  return (
    <Card
      className={cn(
        "my-8 p-5",
        passed ? "border-accent/60 bg-accent/5" : ""
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        {passed ? <Check className="h-5 w-5 text-accent" /> : <Target className="h-5 w-5 text-accent" />}
        <span className="font-serif text-lg">
          Mastery Gate: <span className="font-mono text-sm">{metric} ≥ {threshold}</span>
        </span>
      </div>
      {children && <div className="mb-3 text-sm text-muted-foreground">{children}</div>}
      <Progress value={pct} className="mb-3" />
      <div className="flex items-center gap-2">
        <Input
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={`your ${metric}`}
          className="w-48 font-mono"
        />
        <Button onClick={check} size="sm">Verify</Button>
        {passed && <span className="text-sm font-medium text-accent">Passed. Saved locally.</span>}
        {!passed && lastVal != null && (
          <span className="text-sm text-muted-foreground">
            {lastVal} &lt; {threshold} — not yet
          </span>
        )}
      </div>
    </Card>
  );
}
