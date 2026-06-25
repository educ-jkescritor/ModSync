import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "default" | "high" | "medium" | "low" | "neutral";
};

const tones = {
  default: "border-primary/25 bg-primary/10 text-primary",
  high: "border-danger/25 bg-rose-50 text-danger",
  medium: "border-warning/30 bg-orange-50 text-amber-800",
  low: "border-primary/20 bg-teal-50 text-primary",
  neutral: "border-border bg-muted text-muted-foreground"
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}

