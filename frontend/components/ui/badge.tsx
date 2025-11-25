import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
  size?: "default" | "sm" | "lg"
  dot?: boolean
}

function Badge({
  className,
  variant = "default",
  size = "default",
  dot = false,
  children,
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium transition-all",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          // Size variants
          "px-2.5 py-0.5 text-xs": size === "default",
          "px-2 py-0.5 text-[10px]": size === "sm",
          "px-3 py-1 text-sm": size === "lg",

          // Color variants with enhanced styling
          "border-primary/20 bg-primary/10 text-primary hover:bg-primary/20 shadow-sm":
            variant === "default",
          "border-secondary/20 bg-secondary/50 text-secondary-foreground hover:bg-secondary/60":
            variant === "secondary",
          "border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/20 shadow-sm":
            variant === "destructive",
          "border-border/60 bg-background hover:bg-muted/50 text-foreground shadow-sm":
            variant === "outline",
          "border-success/20 bg-success/10 text-success hover:bg-success/20 shadow-sm":
            variant === "success",
          "border-warning/20 bg-warning/10 text-warning hover:bg-warning/20 shadow-sm":
            variant === "warning",
        },
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            {
              "bg-primary animate-pulse": variant === "default",
              "bg-secondary-foreground": variant === "secondary",
              "bg-destructive animate-pulse": variant === "destructive",
              "bg-foreground": variant === "outline",
              "bg-success animate-pulse": variant === "success",
              "bg-warning animate-pulse": variant === "warning",
            }
          )}
        />
      )}
      {children}
    </div>
  )
}

export { Badge }
