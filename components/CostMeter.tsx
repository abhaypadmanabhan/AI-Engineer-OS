import { DollarSign, Timer, Hash } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

type Props = {
  cost: string;
  latency?: string;
  tokens?: string;
};

export function CostMeter({ cost, latency, tokens }: Props) {
  return (
    <TooltipProvider delayDuration={100}>
      <div className="my-4 inline-flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex items-center gap-1">
              <DollarSign className="h-3 w-3 text-accent" />
              <span className="font-mono text-foreground">{cost}</span>
              <span>/ run</span>
            </span>
          </TooltipTrigger>
          <TooltipContent>Estimated lab cost at current token prices</TooltipContent>
        </Tooltip>
        {latency && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex items-center gap-1">
                <Timer className="h-3 w-3 text-accent" />
                <span className="font-mono text-foreground">{latency}</span>
                <span>p95</span>
              </span>
            </TooltipTrigger>
            <TooltipContent>95th percentile end-to-end latency</TooltipContent>
          </Tooltip>
        )}
        {tokens && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex items-center gap-1">
                <Hash className="h-3 w-3 text-accent" />
                <span className="font-mono text-foreground">{tokens}</span>
                <span>tok</span>
              </span>
            </TooltipTrigger>
            <TooltipContent>Input + output tokens per run</TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
