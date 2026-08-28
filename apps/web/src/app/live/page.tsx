"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  AgentRole,
  SwarmMessageEnvelope,
  SwarmMetrics,
  AGENT_METADATA_MAP,
} from "@/lib/swarm-types";
import { MOCK_SWARM_MESSAGES, INITIAL_SWARM_METRICS } from "@/lib/mock-swarm-data";
import { TrajectoryTurnEvent, FsmState } from "@/lib/types";
import { SwarmMetricsBanner } from "@/components/swarm/swarm-metrics-banner";
import { AgentSwarmNodeMap } from "@/components/swarm/agent-swarm-node-map";
import { AgentSwarmFeed } from "@/components/swarm/agent-swarm-feed";
import { SandboxTerminalPane } from "@/components/replayer/sandbox-terminal-pane";
import { TokenWaterfallChart } from "@/components/charts/token-waterfall-chart";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Activity, Wifi, WifiOff, Cpu, Terminal, Sparkles, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LiveSwarmRunnerPage() {
  const [runnerMode, setRunnerMode] = useState<"instant_replay" | "live_dispatch">("instant_replay");
  const [taskId, setTaskId] = useState<string>("django__django-11099");
  const [taskSuite, setTaskSuite] = useState<string>("SWE_BENCH_VERIFIED");
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(MOCK_SWARM_MESSAGES.length);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [rightPanelTab, setRightPanelTab] = useState<"feed" | "waterfall">("feed");

  // Highlighted file & line from DOM Sync
  const [highlightedFile, setHighlightedFile] = useState<string | null>(null);
  const [highlightedLine, setHighlightedLine] = useState<number | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Active messages subset based on playback step index
  const activeMessages = useMemo(() => {
    return MOCK_SWARM_MESSAGES.slice(0, currentStepIndex);
  }, [currentStepIndex]);

  const latestMessage = activeMessages.length > 0 ? activeMessages[activeMessages.length - 1] : null;

  // Active agent from latest message
  const activeAgent: AgentRole = latestMessage ? latestMessage.fromAgent : "ARCHITECT";

  // Active handoff calculation
  const activeHandoff = useMemo(() => {
    if (!latestMessage || !latestMessage.toAgent || latestMessage.toAgent === "ALL" || latestMessage.toAgent === "DEVELOPER") {
      return null;
    }
    return {
      from: latestMessage.fromAgent,
      to: latestMessage.toAgent as AgentRole | "SANDBOX",
    };
  }, [latestMessage]);

  // Aggregate agent statistics
  const agentStats = useMemo(() => {
    const stats: Record<AgentRole, { turnsCompleted: number; tokensConsumed: number; costUsd: number }> = {
      ARCHITECT: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
      CODER: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
      SUPERVISOR_HEALER: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
      FINOPS_SENTINEL: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
      VOICE_COPILOT: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
      CICD_DAEMON: { turnsCompleted: 0, tokensConsumed: 0, costUsd: 0 },
    };

    activeMessages.forEach((msg) => {
      if (msg.fromAgent in stats) {
        stats[msg.fromAgent].turnsCompleted += 1;
        stats[msg.fromAgent].tokensConsumed += msg.tokensIncurred;
        stats[msg.fromAgent].costUsd += msg.tokenCostUsd;
      }
    });

    return stats;
  }, [activeMessages]);

  // Dynamic Swarm Metrics
  const metrics: SwarmMetrics = useMemo(() => {
    const totalCost = activeMessages.reduce((acc, m) => acc + m.tokenCostUsd, 0);
    const selfHealCount = activeMessages.filter((m) => m.isSelfHealingEvent).length;
    const isComplete = currentStepIndex >= MOCK_SWARM_MESSAGES.length;

    return {
      totalTurns: activeMessages.length,
      totalCostUsd: totalCost,
      cprUsd: totalCost,
      tokenVelocityKps: 1.42,
      activeAgent,
      selfHealingCount: selfHealCount,
      passAt1: isComplete,
      bloatRatioPct: 4.2,
      status: isComplete ? "COMPLETE" : isPlaying ? "RUNNING" : "PAUSED",
    };
  }, [activeMessages, activeAgent, currentStepIndex, isPlaying]);

  // Derived Trajectory Turn Events for Terminal & Waterfall
  const trajectoryTurns: TrajectoryTurnEvent[] = useMemo(() => {
    return activeMessages.map((msg, idx) => ({
      turn_index: idx + 1,
      state: msg.actionType === "PLAN" ? FsmState.REASONING_PLANNER : msg.actionType === "HEAL_PATCH" ? FsmState.SUPERVISOR_AST_HEAL : FsmState.SANDBOX_EXECUTION,
      model_id: AGENT_METADATA_MAP[msg.fromAgent]?.model || "gemini-3.5-flash",
      prompt_tokens: Math.round(msg.tokensIncurred * 0.7),
      completion_tokens: Math.round(msg.tokensIncurred * 0.3),
      reasoning_tokens: msg.fromAgent === "SUPERVISOR_HEALER" || msg.fromAgent === "ARCHITECT" ? 350 : 0,
      turn_cost_usd: msg.tokenCostUsd,
      cumulative_cost_usd: activeMessages.slice(0, idx + 1).reduce((acc, m) => acc + m.tokenCostUsd, 0),
      latency_ms: 320 + idx * 80,
      tool_call_name: msg.actionType === "TOOL_CALL" ? "runPytest" : msg.actionType === "HEAL_PATCH" ? "editHunk" : undefined,
      tool_call_payload: msg.codeDiff ? { path: msg.codeDiff.path, target_content: msg.codeDiff.target_content, replacement_content: msg.codeDiff.replacement_content } : undefined,
      ast_healed: !!msg.isSelfHealingEvent,
      sandbox_exit_code: 0,
      sandbox_stdout: msg.content,
      git_tree_hash: "99a812f88b",
      timestamp: msg.timestamp,
    }));
  }, [activeMessages]);

  const currentTurn = trajectoryTurns.length > 0 ? trajectoryTurns[trajectoryTurns.length - 1] : null;

  // Playback timer loop for instant replay
  useEffect(() => {
    if (runnerMode === "instant_replay" && isPlaying) {
      const stepIntervalMs = Math.max(250, 1200 / playbackSpeed);

      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= MOCK_SWARM_MESSAGES.length) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, stepIntervalMs);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [runnerMode, isPlaying, playbackSpeed]);

  // Listen to Spoken Voice Copilot & Swarm Feed DOM Sync events
  useEffect(() => {
    const handleDomSync = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail) {
        if (customEvent.detail.targetFile) {
          setHighlightedFile(customEvent.detail.targetFile);
        }
        if (customEvent.detail.targetLine !== undefined) {
          setHighlightedLine(customEvent.detail.targetLine);
        }
        // Auto reset highlight after 5 seconds
        setTimeout(() => {
          setHighlightedFile(null);
          setHighlightedLine(null);
        }, 5000);
      }
    };

    window.addEventListener("benchpress:dom-sync", handleDomSync);
    return () => window.removeEventListener("benchpress:dom-sync", handleDomSync);
  }, []);

  const handleTogglePlay = () => {
    if (currentStepIndex >= MOCK_SWARM_MESSAGES.length) {
      setCurrentStepIndex(1);
      setIsPlaying(true);
    } else {
      setIsPlaying((prev) => !prev);
    }
  };

  const handleReset = () => {
    setCurrentStepIndex(1);
    setIsPlaying(false);
  };

  const handleSelectMessage = (msg: SwarmMessageEnvelope) => {
    setSelectedMessageId(msg.id);
    if (msg.targetFile) {
      setHighlightedFile(msg.targetFile);
    }
    if (msg.targetLine) {
      setHighlightedLine(msg.targetLine);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge variant="cyan" dot size="sm">
              MULTI-AGENT SWARM RUNTIME
            </Badge>
            <span className="text-xs text-zinc-500 font-mono">
              6 Specialized Cooperating Agents
            </span>
            {runnerMode === "live_dispatch" && wsConnected ? (
              <Badge variant="emerald" size="sm">
                <Wifi className="h-3 w-3 inline mr-1" /> WebSocket Live
              </Badge>
            ) : (
              <Badge variant="neutral" size="sm">
                <WifiOff className="h-3 w-3 inline mr-1" /> Deterministic Replay
              </Badge>
            )}
          </div>
          <h1 className="text-2xl font-extrabold text-white sm:text-3xl font-mono tracking-tight flex items-center gap-2.5">
            Interactive Multi-Agent Swarm Visualizer
            <Sparkles className="w-6 h-6 text-cyan-400" />
          </h1>
          <p className="mt-1 text-sm text-zinc-400 font-sans">
            Real-time visualization of 6 specialized agents debating, delegating code edits, healing AST schema errors, and enforcing FinOps budget ceilings.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="md">
            gVisor Sandbox: HEALTHY
          </Badge>
          <Badge variant="cyan" size="md">
            BigQuery Write: STREAMING
          </Badge>
        </div>
      </div>

      {/* 1. Top Section: Swarm Metrics & Playback Controls Banner */}
      <SwarmMetricsBanner
        metrics={metrics}
        taskId={taskId}
        taskSuite={taskSuite}
        runnerMode={runnerMode}
        onChangeRunnerMode={(mode) => {
          setRunnerMode(mode);
          if (mode === "instant_replay") {
            setCurrentStepIndex(1);
            setIsPlaying(true);
          }
        }}
        isPlaying={isPlaying}
        onTogglePlay={handleTogglePlay}
        onReset={handleReset}
        playbackSpeed={playbackSpeed}
        onChangeSpeed={setPlaybackSpeed}
      />

      {/* 2. Middle Section: Interactive Glowing SVG Node Topology Map */}
      <AgentSwarmNodeMap
        activeAgent={activeAgent}
        activeHandoff={activeHandoff}
        agentStats={agentStats}
        onSelectAgent={(role) => {
          // Filter or highlight that agent
        }}
      />

      {/* 3. Bottom Section: Split-View Virtual Sandbox Terminal (Left) vs Swarm Feed & Token Waterfall (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (50%): Virtual Sandbox Terminal */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-300 font-semibold uppercase">
              <Terminal className="h-4 w-4 text-[#00F0FF]" />
              Isolated Execution Sandbox (gVisor)
            </div>
            <span className="text-[11px] font-mono text-zinc-500">
              Turn {currentTurn?.turn_index || 1} / {MOCK_SWARM_MESSAGES.length}
            </span>
          </div>

          <SandboxTerminalPane
            currentTurn={currentTurn}
            highlightedFile={highlightedFile}
            highlightedLine={highlightedLine}
            activeTool={latestMessage?.actionType === "TOOL_CALL" ? "runPytest" : latestMessage?.codeDiff ? "editHunk" : null}
          />
        </div>

        {/* Right Column (50%): Agent Swarm Communications Feed & Token Waterfall */}
        <div className="lg:col-span-6 space-y-3">
          {/* Tabs header */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-[#0A0D14] p-0.5 text-xs font-mono">
              <button
                onClick={() => setRightPanelTab("feed")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1 rounded-md transition font-semibold",
                  rightPanelTab === "feed"
                    ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/30 shadow-glass-cyan"
                    : "text-zinc-400 hover:text-white"
                )}
              >
                <Activity className="h-3 w-3 text-[#00F0FF]" />
                Swarm Feed ({activeMessages.length})
              </button>
              <button
                onClick={() => setRightPanelTab("waterfall")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1 rounded-md transition font-semibold",
                  rightPanelTab === "waterfall"
                    ? "bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30 shadow-glass-emerald"
                    : "text-zinc-400 hover:text-white"
                )}
              >
                <BarChart2 className="h-3 w-3 text-[#10B981]" />
                Token Burn Waterfall
              </button>
            </div>

            <span className="text-[11px] font-mono text-zinc-500">
              1-Click Code Diff Sync
            </span>
          </div>

          {rightPanelTab === "feed" ? (
            <AgentSwarmFeed
              messages={activeMessages}
              selectedMessageId={selectedMessageId}
              onSelectMessage={handleSelectMessage}
            />
          ) : (
            <div className="h-[580px] rounded-xl border border-white/10 bg-[#0A0D14]/90 p-4 backdrop-blur-2xl shadow-2xl flex flex-col justify-between">
              <TokenWaterfallChart turns={trajectoryTurns} />
              <div className="text-[11px] font-mono text-zinc-400 border-t border-white/10 pt-3 flex items-center justify-between">
                <span>Total Accumulated Tokens:</span>
                <span className="text-[#00F0FF] font-bold">
                  {trajectoryTurns.reduce((acc, t) => acc + t.prompt_tokens + t.completion_tokens, 0).toLocaleString()} tokens
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
