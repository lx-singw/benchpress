"use client";

import React from "react";

interface ModelBadgeProps {
  provider: string;
  className?: string;
}

export function ModelBadge({ provider, className = "" }: ModelBadgeProps) {
  let badgeStyle = "border-white/10 bg-white/5 text-zinc-300";

  if (provider === "Benchpress Hybrid") {
    badgeStyle = "border-emerald-500/40 bg-emerald-500/15 text-emerald-300 shadow-sm shadow-emerald-950";
  } else if (provider === "Google") {
    badgeStyle = "border-[#00F0FF]/40 bg-[#00F0FF]/15 text-[#00F0FF]";
  } else if (provider === "Anthropic") {
    badgeStyle = "border-amber-500/40 bg-amber-500/15 text-amber-300";
  } else if (provider === "OpenAI") {
    badgeStyle = "border-purple-500/40 bg-purple-500/15 text-purple-300";
  } else if (provider === "Meta") {
    badgeStyle = "border-blue-500/40 bg-blue-500/15 text-blue-300";
  } else if (provider === "DeepSeek") {
    badgeStyle = "border-cyan-500/40 bg-cyan-500/15 text-cyan-300";
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${badgeStyle} ${className}`}
    >
      {provider}
    </span>
  );
}
