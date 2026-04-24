import { AlertTriangle, Info, Skull, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

type Kind = "info" | "warn" | "break" | "tip";
const styles: Record<Kind, { cls: string; Icon: any; label: string }> = {
  info:  { cls: "border-sky-500/40 bg-sky-500/5",    Icon: Info,          label: "Note" },
  warn:  { cls: "border-amber-500/40 bg-amber-500/5", Icon: AlertTriangle, label: "Warning" },
  break: { cls: "border-rose-500/40 bg-rose-500/5",   Icon: Skull,         label: "Watch it break" },
  tip:   { cls: "border-emerald-500/40 bg-emerald-500/5", Icon: Zap,       label: "Tip" },
};

export function Callout({
  kind = "info",
  title,
  children,
}: {
  kind?: Kind;
  title?: string;
  children: React.ReactNode;
}) {
  const { cls, Icon, label } = styles[kind];
  return (
    <div className={cn("my-5 rounded-lg border p-4", cls)}>
      <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
        <Icon className="h-4 w-4" />
        {title ?? label}
      </div>
      <div className="text-sm">{children}</div>
    </div>
  );
}
