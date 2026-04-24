import { DollarSign, Timer, Hash } from "lucide-react";

type Props = {
  cost: string;         // "$0.04"
  latency?: string;     // "1.8s"
  tokens?: string;      // "12k"
};

export function CostMeter({ cost, latency, tokens }: Props) {
  return (
    <div className="my-4 inline-flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
      <span className="inline-flex items-center gap-1">
        <DollarSign className="h-3 w-3 text-accent" />
        <span className="font-mono text-foreground">{cost}</span>
        <span>/ run</span>
      </span>
      {latency && (
        <span className="inline-flex items-center gap-1">
          <Timer className="h-3 w-3 text-accent" />
          <span className="font-mono text-foreground">{latency}</span>
          <span>p95</span>
        </span>
      )}
      {tokens && (
        <span className="inline-flex items-center gap-1">
          <Hash className="h-3 w-3 text-accent" />
          <span className="font-mono text-foreground">{tokens}</span>
          <span>tok</span>
        </span>
      )}
    </div>
  );
}
