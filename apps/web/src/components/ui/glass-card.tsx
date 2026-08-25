import React from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  glow?: "cyan" | "emerald" | "amber" | "crimson" | "none";
  hoverEffect?: boolean;
}

export function GlassCard({
  children,
  className,
  glow = "none",
  hoverEffect = false,
  ...props
}: GlassCardProps) {
  const glowClasses = {
    none: "border-white/10 bg-[#121722]/75",
    cyan: "border-[#00F0FF]/30 bg-[#121722]/85 shadow-glass-cyan",
    emerald: "border-[#10B981]/30 bg-[#121722]/85 shadow-glass-emerald",
    amber: "border-[#F59E0B]/30 bg-[#121722]/85 shadow-glass-amber",
    crimson: "border-[#EF4444]/30 bg-[#121722]/85 shadow-glass-crimson",
  };

  return (
    <div
      className={cn(
        "relative rounded-xl border backdrop-blur-xl transition-all duration-300",
        glowClasses[glow],
        hoverEffect && "hover:border-[#00F0FF]/50 hover:bg-[#1A2234]/80 hover:shadow-glass-cyan",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
