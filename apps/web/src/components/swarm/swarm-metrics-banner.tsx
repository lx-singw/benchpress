"use client";

import React from "react";
import { SwarmMetrics, AGENT_METADATA_MAP } from "@/lib/swarm-types";
import { AgentBadge } from "./agent-badge";
import { formatUsd, formatPercent } from "@/lib/utils";
import {
  Activity,
  Flame,
  ShieldCheck,
  Sparkles,
  Zap,
  TrendingDown,
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SwarmMetricsBannerProps {
  metrics: SwarmMetrics;
  taskId: string;
  taskSuite: string;
  runnerMode: "instant_replay" | "live_dispatch";
  onChangeRunnerMode: (mode: "instant_replay" | "live_dispatch") => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onReset: () => void;
  playbackSpeed: number;
  onChangeSpeed: (speed: number) => void;
  className?: string;
}

export function SwarmMetricsBanner({
  metrics,
  taskId,
  taskSuite,
  runnerMode,
  onChangeRunnerMode,
  isPlaying,
  onTogglePlay,
  onReset,
  playbackSpeed,
  onChangeSpeed,
  className,
}: SwarmMetricsBannerProps) {
  const activeMeta = AGENT_METADATA_MAP[metrics.activeAgent] || AGENT_METADATA_MAP.ARCHITECT;

  return (
    <div
      className={cn(
        "rounded-xl border border-white/10 bg-[#0A0D14]/90 p-4 backdrop-blur-2xl shadow-2xl space-y-4 font-mono select-none",
        className
      )}
    >
      {/* Top Bar: Title, Task ID, Mode Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/10 pb-4">
        {/* Left: Task & Swarm Status */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ backgroundColor: activeMeta.color }}
              />
              <span
                className="relative inline-flex rounded-full h-2.5 w-2.5"
                style={{ backgroundColor: activeMeta.color }}
              />
            </span>
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Swarm Execution Engine
            </span>
          </div>

          <span className="rounded bg-black/50 px-2 py-0.5 text-xs text-zinc-300 border border-white/10 font-bold">
            {taskId}
          </span>

          <span className="rounded bg-white/5 px-2 py-0.5 text-[11px] text-zinc-400 border border-white/5">
            {taskSuite}
          </span>
        </div>

        {/* Right: Mode Switcher & Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Mode Switcher */}
          <div className="flex rounded-lg border border-white/10 bg-black/60 p-0.5 text-xs">
            <button
              onClick={() => onChangeRunnerMode("instant_replay")}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md transition font-semibold",
                runnerMode === "instant_replay"
                  ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/30 shadow-glass-cyan"
                  : "text-zinc-400 hover:text-white"
              )}
            >
              <Zap className="h-3 w-3 text-[#00F0FF]" />
              15s Replay
            </button>
            <button
              onClick={() => onChangeRunnerMode("live_dispatch")}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md transition font-semibold",
                runnerMode === "live_dispatch"
                  ? "bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30 shadow-glass-emerald"
                  : "text-zinc-400 hover:text-white"
              )}
            >
              <Cpu className="h-3 w-3 text-[#10B981]" />
              Cloud Tasks
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex rounded-lg border border-white/10 bg-black/60 p-0.5 text-xs">
            {[1, 2, 4].map((spd) => (
              <button
                key={spd}
                onClick={() => onChangeSpeed(spd)}
                className={cn(
                  "px-2 py-1 rounded-md text-[10px] font-bold transition",
                  playbackSpeed === spd
                    ? "bg-white/20 text-white"
                    : "text-zinc-500 hover:text-zinc-300"
                )}
              >
                {spd}x
              </button>
            ))}
          </div>

          {/* Play/Pause Button */}
          <button
            onClick={onTogglePlay}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#00F0FF] to-[#10B981] text-[#0A0D14] font-bold text-xs hover:opacity-95 transition shadow-glass-cyan"
          >
            {isPlaying ? (
              <>
                <Pause className="h-3.5 w-3.5" /> Pause
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" /> {metrics.totalTurns >= 18 ? "Restart" : "Play"}
              </>
            )}
          </button>

          {/* Reset Button */}
          <button
            onClick={onReset}
            className="p-1.5 rounded-lg border border-white/10 bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 transition"
            title="Reset to Turn 1"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row: 6 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* KPI 1: Active Agent */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <Activity className="h-3 w-3 text-[#00F0FF]" /> Active Node
          </div>
          <div className="mt-1">
            <AgentBadge role={metrics.activeAgent} size="sm" isActive={isPlaying} />
          </div>
        </div>

        {/* KPI 2: Swarm Turns */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <Flame className="h-3 w-3 text-amber-400" /> Swarm Turns
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-lg font-bold text-white">{metrics.totalTurns}</span>
            <span className="text-xs text-zinc-500">/ 18</span>
          </div>
        </div>

        {/* KPI 3: Accumulated Spend */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <TrendingDown className="h-3 w-3 text-[#00F0FF]" /> Trajectory Spend
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-lg font-bold text-[#00F0FF]">
              {formatUsd(metrics.totalCostUsd)}
            </span>
            <span className="text-[10px] text-emerald-400 font-bold">-96.7%</span>
          </div>
        </div>

        {/* KPI 4: Token Velocity */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <Zap className="h-3 w-3 text-purple-400" /> Velocity
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-lg font-bold text-purple-300">{metrics.tokenVelocityKps}</span>
            <span className="text-[10px] text-zinc-500">k tok/s</span>
          </div>
        </div>

        {/* KPI 5: AST Self-Healed */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-amber-400" /> AST Heals
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-lg font-bold text-amber-300">{metrics.selfHealingCount}</span>
            <span className="text-[10px] text-amber-400/80">auto-patched</span>
          </div>
        </div>

        {/* KPI 6: Pass@1 Outcome */}
        <div className="p-3 rounded-lg border border-white/5 bg-[#121722]/60 flex flex-col justify-between">
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-[#10B981]" /> Pass@1
          </div>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="text-lg font-bold text-[#10B981]">
              {metrics.passAt1 ? "VERIFIED" : "EVALUATING"}
            </span>
            {metrics.passAt1 && <ShieldCheck className="h-4 w-4 text-[#10B981]" />}
          </div>
        </div>
      </div>
    </div>
  );
}
