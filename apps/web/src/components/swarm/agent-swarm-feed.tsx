"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  AgentRole,
  SwarmMessageEnvelope,
  AGENT_METADATA_MAP,
  SwarmActionType,
} from "@/lib/swarm-types";
import { AgentBadge } from "./agent-badge";
import { cn, formatUsd } from "@/lib/utils";
import {
  Sparkles,
  ArrowRight,
  Filter,
  Code2,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Activity,
  Maximize2,
} from "lucide-react";

interface AgentSwarmFeedProps {
  messages: SwarmMessageEnvelope[];
  selectedMessageId?: string | null;
  onSelectMessage?: (msg: SwarmMessageEnvelope) => void;
  className?: string;
}

const ACTION_CONFIG: Record<
  SwarmActionType,
  { label: string; bg: string; text: string; border: string }
> = {
  PLAN: {
    label: "PLAN",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
  },
  TOOL_CALL: {
    label: "TOOL CALL",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  TOOL_RESULT: {
    label: "TOOL RESULT",
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    border: "border-sky-500/30",
  },
  HEAL_PATCH: {
    label: "AST HEAL",
    bg: "bg-amber-500/15",
    text: "text-amber-300 font-bold",
    border: "border-amber-500/40",
  },
  SENTINEL_AUDIT: {
    label: "FINOPS AUDIT",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/30",
  },
  VOICE_DIAGNOSTIC: {
    label: "VOICE COPILOT",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/30",
  },
  PR_CREATED: {
    label: "PR GENERATED",
    bg: "bg-sky-500/15",
    text: "text-sky-300 font-bold",
    border: "border-sky-500/40",
  },
};

export function AgentSwarmFeed({
  messages,
  selectedMessageId,
  onSelectMessage,
  className,
}: AgentSwarmFeedProps) {
  const [roleFilter, setRoleFilter] = useState<AgentRole | "ALL">("ALL");
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const filteredMessages =
    roleFilter === "ALL"
      ? messages
      : messages.filter((m) => m.fromAgent === roleFilter);

  useEffect(() => {
    if (autoScroll && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [filteredMessages.length, autoScroll]);

  const handleMessageClick = (msg: SwarmMessageEnvelope) => {
    if (onSelectMessage) {
      onSelectMessage(msg);
    }
    // Also dispatch custom DOM event for other listeners
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("benchpress:dom-sync", {
          detail: {
            action: "HIGHLIGHT_TURN",
            targetTurn: msg.turnNumber,
            targetFile: msg.targetFile,
            targetLine: msg.targetLine,
            codeDiff: msg.codeDiff,
          },
        })
      );
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col h-[580px] rounded-xl border border-white/10 bg-[#0A0D14]/90 backdrop-blur-2xl shadow-2xl overflow-hidden font-mono",
        className
      )}
    >
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 bg-[#121722]/80 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-[#00F0FF]" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Inter-Agent Swarm Communications
          </h3>
          <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-zinc-300 font-semibold">
            {filteredMessages.length} events
          </span>
        </div>

        {/* Auto Scroll Toggle */}
        <div className="flex items-center gap-2 text-[10px] text-zinc-400">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-[#00F0FF] rounded cursor-pointer"
            />
            <span>Auto-Scroll</span>
          </label>
        </div>
      </div>

      {/* Role Filter Pills */}
      <div className="flex items-center gap-1.5 px-4 py-2 bg-[#0A0D14] border-b border-white/5 overflow-x-auto text-[11px] no-scrollbar">
        <span className="text-zinc-500 flex items-center gap-1 text-[10px] pr-1">
          <Filter className="h-3 w-3" /> Filter:
        </span>

        <button
          onClick={() => setRoleFilter("ALL")}
          className={cn(
            "px-2.5 py-1 rounded-full border text-[10px] font-semibold transition-all whitespace-nowrap",
            roleFilter === "ALL"
              ? "border-[#00F0FF]/50 bg-[#00F0FF]/15 text-[#00F0FF] shadow-glass-cyan"
              : "border-white/5 bg-white/[0.02] text-zinc-400 hover:text-white"
          )}
        >
          All ({messages.length})
        </button>

        {(
          [
            "ARCHITECT",
            "CODER",
            "SUPERVISOR_HEALER",
            "FINOPS_SENTINEL",
            "VOICE_COPILOT",
            "CICD_DAEMON",
          ] as AgentRole[]
        ).map((role) => {
          const meta = AGENT_METADATA_MAP[role];
          const count = messages.filter((m) => m.fromAgent === role).length;
          const isSelected = roleFilter === role;

          return (
            <button
              key={role}
              onClick={() => setRoleFilter(role)}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-semibold transition-all whitespace-nowrap",
                isSelected
                  ? `${meta.badgeBorderClass} ${meta.badgeBgClass} ${meta.badgeTextClass} ${meta.badgeGlowClass}`
                  : "border-white/5 bg-white/[0.02] text-zinc-400 hover:text-white"
              )}
            >
              <span>{meta.emoji}</span>
              <span>{meta.shortName}</span>
              <span className="opacity-60 text-[9px]">({count})</span>
            </button>
          );
        })}
      </div>

      {/* Messages Stream */}
      <div
        ref={scrollContainerRef}
        className="flex-1 p-4 overflow-y-auto space-y-3 selection:bg-[#00F0FF]/30"
      >
        {filteredMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs gap-2">
            <Zap className="h-6 w-6 opacity-30 text-[#00F0FF]" />
            <span>No swarm communication events recorded for this filter.</span>
          </div>
        ) : (
          filteredMessages.map((msg) => {
            const fromMeta = AGENT_METADATA_MAP[msg.fromAgent];
            const actionCfg = ACTION_CONFIG[msg.actionType] || ACTION_CONFIG.PLAN;
            const isSelected = selectedMessageId === msg.id;

            return (
              <div
                key={msg.id}
                onClick={() => handleMessageClick(msg)}
                className={cn(
                  "p-3.5 rounded-xl border transition-all duration-200 cursor-pointer group relative overflow-hidden",
                  isSelected
                    ? "border-[#00F0FF] bg-[#00F0FF]/10 shadow-glass-cyan"
                    : msg.isSelfHealingEvent
                    ? "border-amber-500/40 bg-amber-950/20 hover:border-amber-400/60"
                    : "border-white/5 bg-[#121722]/70 hover:border-white/20 hover:bg-[#1A2234]/70"
                )}
              >
                {/* Self-Healing Glow Accent */}
                {msg.isSelfHealingEvent && (
                  <div className="absolute top-0 right-0 px-2 py-0.5 rounded-bl-lg bg-gradient-to-l from-amber-500/30 to-transparent text-[9px] font-bold text-amber-300 flex items-center gap-1 border-b border-l border-amber-500/30">
                    <Sparkles className="h-2.5 w-2.5 text-amber-400" />
                    AUTONOMOUS AST HEAL
                  </div>
                )}

                {/* Top Metadata Row */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-[11px]">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* From Agent Badge */}
                    <AgentBadge role={msg.fromAgent} size="sm" showModel={false} />

                    {/* Handoff Arrow */}
                    {msg.toAgent && msg.toAgent !== "ALL" && (
                      <span className="text-zinc-500 flex items-center gap-1 text-[10px]">
                        <ArrowRight className="h-3 w-3" />
                        <span className="font-semibold text-zinc-300">
                          {msg.toAgent === "SANDBOX"
                            ? "📦 Sandbox"
                            : msg.toAgent === "DEVELOPER"
                            ? "👤 Developer"
                            : AGENT_METADATA_MAP[msg.toAgent]?.shortName || msg.toAgent}
                        </span>
                      </span>
                    )}

                    {/* Action Type Pill */}
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[9px] font-bold border uppercase tracking-wider",
                        actionCfg.bg,
                        actionCfg.text,
                        actionCfg.border
                      )}
                    >
                      {actionCfg.label}
                    </span>
                  </div>

                  {/* Right side: Turn + Timestamp + Cost */}
                  <div className="flex items-center gap-2.5 text-[10px] text-zinc-400">
                    <span className="text-zinc-500">{msg.timestamp}</span>
                    <span className="rounded bg-black/40 px-1.5 py-0.5 text-zinc-300 border border-white/5">
                      Turn {msg.turnNumber}
                    </span>
                    <span className="text-[#00F0FF] font-semibold">{formatUsd(msg.tokenCostUsd)}</span>
                  </div>
                </div>

                {/* Message Speech / Thought Content */}
                <p className="text-xs text-zinc-200 font-sans leading-relaxed selection:bg-[#00F0FF]/30">
                  {msg.content}
                </p>

                {/* Code Diff Box Preview if present */}
                {msg.codeDiff && (
                  <div className="mt-2.5 rounded-lg border border-white/10 bg-black/70 p-2.5 text-[11px] font-mono space-y-1">
                    <div className="flex items-center justify-between text-zinc-400 text-[10px] border-b border-white/5 pb-1 mb-1">
                      <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                        <FileCode className="h-3 w-3" /> {msg.codeDiff.path}
                      </span>
                      {msg.codeDiff.lines && <span>Lines {msg.codeDiff.lines}</span>}
                    </div>

                    {msg.codeDiff.target_content && (
                      <div className="text-rose-400 bg-rose-950/20 px-2 py-0.5 rounded border border-rose-500/20 truncate">
                        - {msg.codeDiff.target_content}
                      </div>
                    )}
                    {msg.codeDiff.replacement_content && (
                      <div className="text-emerald-400 bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20 truncate">
                        + {msg.codeDiff.replacement_content}
                      </div>
                    )}
                  </div>
                )}

                {/* Bottom Footer: 1-Click Sync Hint */}
                <div className="mt-2.5 flex items-center justify-between text-[9px] text-zinc-500 border-t border-white/5 pt-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                  <span className="flex items-center gap-1 text-zinc-400">
                    <Code2 className="h-3 w-3 text-[#00F0FF]" /> Click to sync diff with terminal
                  </span>
                  <span>{msg.tokensIncurred} tokens</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
