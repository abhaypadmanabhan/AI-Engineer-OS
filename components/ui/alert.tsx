import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg~*]:pl-7",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground border-border",
        info: "border-accent/40 bg-accent/10 text-foreground [&>svg]:text-accent",
        warning: "border-yellow-500/40 bg-yellow-500/10 text-foreground [&>svg]:text-yellow-400",
        destructive: "border-destructive/50 bg-destructive/10 text-destructive-foreground [&>svg]:text-destructive",
        break: "border-red-500/40 bg-red-500/10 text-foreground [&>svg]:text-red-400",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export const Alert = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>>(
  ({ className, variant, ...props }, ref) => (
    <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
  )
);
Alert.displayName = "Alert";

export const AlertTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...p }, ref) => (
    <h5 ref={ref} className={cn("mb-1 font-semibold leading-none tracking-tight", className)} {...p} />
  )
);
AlertTitle.displayName = "AlertTitle";

export const AlertDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...p }, ref) => <div ref={ref} className={cn("text-sm [&_p]:leading-relaxed", className)} {...p} />
);
AlertDescription.displayName = "AlertDescription";
