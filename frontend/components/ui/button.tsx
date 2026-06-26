import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "ghost" | "danger" | "outline";
  size?: "default" | "icon" | "sm";
};

const variants = {
  default: "border-transparent bg-primary text-primary-foreground hover:bg-teal-800",
  secondary: "border-transparent bg-muted text-foreground hover:bg-slate-200",
  ghost: "border-transparent bg-transparent text-foreground hover:bg-muted",
  danger: "border-transparent bg-danger text-white hover:bg-rose-700",
  outline: "border-border bg-white text-foreground hover:bg-slate-50"
};

const sizes = {
  default: "h-10 px-4",
  sm: "h-8 px-3 text-sm",
  icon: "h-10 w-10 p-0"
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);


Button.displayName = "Button";

