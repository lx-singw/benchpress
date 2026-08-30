import React from "react";
import { CheckCircle2, ShieldCheck, Zap, FlaskConical } from "lucide-react";

export type TruthClassVariant =
  | "BENCHPRESS_MEASURED"
  | "OBSERVED"
  | "OFFICIAL_SPECIFICATION"
  | "PROJECTED"
  | "ILLUSTRATIVE"
  | "DEMO_FIXTURE";

interface TruthBadgeProps {
  truthClass?: TruthClassVariant | string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function TruthBadge({
  truthClass = "DEMO_FIXTURE",
  size = "md",
  className = "",
}: TruthBadgeProps) {
  const normalized = truthClass.toUpperCase().replace(/\s+/g, "_");

  let label = "OBSERVED";
  let icon = <CheckCircle2 className="w-3.5 h-3.5" />;
  let colorClasses =
    "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.15)]";

  if (normalized === "BENCHPRESS_MEASURED" || normalized === "OBSERVED") {
    label = "GROUND TRUTH: OBSERVED";
    icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
    colorClasses =
      "bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-[0_0_20px_rgba(16,185,129,0.2)]";
  } else if (normalized === "OFFICIAL_SPECIFICATION") {
    label = "OFFICIAL SPECIFICATION";
    icon = <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />;
    colorClasses =
      "bg-cyan-500/15 text-cyan-300 border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.2)]";
  } else if (normalized === "PROJECTED") {
    label = "PROJECTED ESTIMATE";
    icon = <Zap className="w-3.5 h-3.5 text-amber-400" />;
    colorClasses =
      "bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.2)]";
  } else if (normalized === "DEMO_FIXTURE" || normalized === "ILLUSTRATIVE") {
    label = "DEMO FIXTURE";
    icon = <FlaskConical className="w-3.5 h-3.5 text-purple-400" />;
    colorClasses =
      "bg-purple-500/15 text-purple-300 border-purple-500/40 shadow-[0_0_20px_rgba(168,85,247,0.2)]";
  }

  const sizeClasses = {
    sm: "text-[10px] px-2 py-0.5 gap-1 tracking-wider",
    md: "text-xs px-2.5 py-1 gap-1.5 font-medium tracking-wide",
    lg: "text-sm px-3.5 py-1.5 gap-2 font-semibold tracking-wide",
  }[size];

  return (
    <div
      className={`inline-flex items-center rounded-full border backdrop-blur-md font-mono uppercase select-none transition-all duration-300 ${colorClasses} ${sizeClasses} ${className}`}
    >
      {icon}
      <span>{label}</span>
    </div>
  );
}
