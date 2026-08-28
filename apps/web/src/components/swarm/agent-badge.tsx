"use client";

import React, { useState } from "react";
import { AgentRole, AGENT_METADATA_MAP } from "@/lib/swarm-types";
import { cn } from "@/lib/utils";

interface AgentBadgeProps {
  role: AgentRole;
  size?: "sm" | "md" | "lg";
  isActive?: boolean;
  isThinking?: boolean;
  showModel?: boolean;
  showStatus?: boolean;
  className?: string;
  onClick?: () => void;
}

export function AgentBadge({
  role,
  size = "md",
  isActive = false,
  isThinking = false,
  showModel = true,
  showStatus = true,
  className,
  onClick,
}: AgentBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const meta = AGENT_METADATA_MAP[role] || AGENT_METADATA_MAP.ARCHITECT;

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] gap-1.5",
    md: "px-2.5 py-1 text-xs gap-2",
    lg: "px-3.5 py-1.5 text-sm gap-2.5",
  };

  const emojiSizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div
        onClick={onClick}
        className={cn(
          "inline-flex items-center rounded-full border font-mono transition-all duration-300 backdrop-blur-md cursor-pointer select-none",
          sizeStyles[size],
          meta.badgeBorderClass,
          meta.badgeBgClass,
          meta.badgeTextClass,
          isActive
            ? `${meta.badgeGlowClass} border-current ring-1 ring-white/20 animate-pulse`
            : "hover:border-white/30 hover:bg-white/[0.06]",
          className
        )}
      >
        {/* Status Indicator Dot */}
        {showStatus && (
          <span className="relative flex h-2 w-2">
            {isActive && (
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ backgroundColor: meta.color }}
              />
            )}
            <span
              className={cn(
                "relative inline-flex rounded-full h-2 w-2",
                isActive ? "opacity-100" : "opacity-40"
              )}
              style={{ backgroundColor: meta.color }}
            />
          </span>
        )}

        {/* Emoji Avatar */}
        <span className={emojiSizes[size]}>{meta.emoji}</span>

        {/* Display Name */}
        <span className="font-semibold tracking-wide">{meta.shortName}</span>

        {/* Model Pill */}
        {showModel && (
          <span className="rounded bg-black/40 px-1.5 py-0.2 text-[9px] font-normal text-zinc-300 border border-white/5">
            {meta.model}
          </span>
        )}

        {/* Thinking Indicator */}
        {isThinking && (
          <span className="animate-spin text-[10px]" style={{ color: meta.color }}>
            ⟳
          </span>
        )}
      </div>

      {/* Interactive Tooltip Popover */}
      {showTooltip && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 rounded-xl border border-white/15 bg-[#0A0D14]/95 backdrop-blur-2xl shadow-2xl text-left pointer-events-none animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center gap-2 border-b border-white/10 pb-2 mb-2">
            <span className="text-lg">{meta.emoji}</span>
            <div>
              <div className="text-xs font-bold text-white font-mono">{meta.displayName}</div>
              <div className="text-[10px] text-zinc-400 font-mono">{meta.model}</div>
            </div>
          </div>
          <p className="text-[11px] text-zinc-300 font-sans leading-relaxed mb-1.5">
            {meta.description}
          </p>
          <div className="text-[10px] text-zinc-400 font-mono pt-1.5 border-t border-white/5">
            <span className="text-zinc-500 font-semibold">Responsibility:</span> {meta.responsibility}
          </div>
        </div>
      )}
    </div>
  );
}
