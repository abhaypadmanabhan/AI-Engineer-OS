import { AlertTriangle, Info, Skull, Zap } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

type Kind = "info" | "warn" | "warning" | "break" | "tip";
const variantMap: Record<Kind, { variant: "info" | "warning" | "break" | "default"; Icon: typeof Info; label: string }> = {
  info:    { variant: "info",    Icon: Info,          label: "Note" },
  warn:    { variant: "warning", Icon: AlertTriangle, label: "Warning" },
  warning: { variant: "warning", Icon: AlertTriangle, label: "Warning" },
  break:   { variant: "break",   Icon: Skull,         label: "Watch it break" },
  tip:     { variant: "default", Icon: Zap,           label: "Tip" },
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
  const entry = variantMap[kind] ?? variantMap.info;
  const { variant, Icon, label } = entry;
  return (
    <Alert variant={variant} className="my-5">
      <Icon className="h-4 w-4" />
      <AlertTitle className="text-xs font-semibold uppercase tracking-wide">{title ?? label}</AlertTitle>
      <AlertDescription className="mt-1 text-sm">{children}</AlertDescription>
    </Alert>
  );
}
