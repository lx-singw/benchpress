import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "cyan" | "emerald" | "amber" | "crimson" | "purple" | "sky" | "rose" | "neutral";
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  children,
  variant = "neutral",
  size = "md",
  dot = false,
  className,
  ...props
}: BadgeProps) {
  const variantStyles = {
    cyan: "bg-[#00F0FF]/10 text-[#00F0FF] border-[#00F0FF]/30",
    emerald: "bg-[#10B981]/10 text-[#10B981] border-[#10B981]/30",
    amber: "bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30",
    crimson: "bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30",
    purple: "bg-[#8B5CF6]/10 text-[#8B5CF6] border-[#8B5CF6]/30",
    sky: "bg-[#38BDF8]/10 text-[#38BDF8] border-[#38BDF8]/30",
    rose: "bg-[#F43F5E]/10 text-[#F43F5E] border-[#F43F5E]/30",
    neutral: "bg-gray-800/60 text-gray-300 border-gray-700/50",
  };

  const dotColors = {
    cyan: "bg-[#00F0FF]",
    emerald: "bg-[#10B981]",
    amber: "bg-[#F59E0B]",
    crimson: "bg-[#EF4444]",
    purple: "bg-[#8B5CF6]",
    sky: "bg-[#38BDF8]",
    rose: "bg-[#F43F5E]",
    neutral: "bg-gray-400",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs font-medium",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-mono tracking-wide",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn("h-1.5 w-1.5 rounded-full animate-pulse", dotColors[variant])}
        />
      )}
      {children}
    </span>
  );
}
