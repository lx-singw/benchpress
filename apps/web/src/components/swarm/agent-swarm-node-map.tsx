"use client";

import React, { useState } from "react";
import { AgentRole, AGENT_METADATA_MAP } from "@/lib/swarm-types";
import { cn, formatUsd } from "@/lib/utils";

interface AgentSwarmNodeMapProps {
  activeAgent: AgentRole;
  activeHandoff?: { from: AgentRole; to: AgentRole | "SANDBOX" } | null;
  agentStats?: Record<AgentRole, { turnsCompleted: number; tokensConsumed: number; costUsd: number }>;
  onSelectAgent?: (role: AgentRole) => void;
  className?: string;
}

interface NodePosition {
  id: AgentRole | "SANDBOX";
  label: string;
  sublabel: string;
  emoji: string;
  x: number;
  y: number;
  color: string;
  glow: string;
}

const NODES: NodePosition[] = [
  {
    id: "ARCHITECT",
    label: "Architect",
    sublabel: "Gemini 2.5 Pro",
    emoji: "🧠",
    x: 120,
    y: 150,
    color: "#00F0FF",
    glow: "rgba(0, 240, 255, 0.4)",
  },
  {
    id: "FINOPS_SENTINEL",
    label: "FinOps Sentinel",
    sublabel: "Markov Governor",
    emoji: "🛡️",
    x: 390,
    y: 45,
    color: "#8B5CF6",
    glow: "rgba(139, 92, 246, 0.4)",
  },
  {
    id: "CODER",
    label: "Coder Agent",
    sublabel: "Gemini 3.5 Flash",
    emoji: "⚡",
    x: 390,
    y: 150,
    color: "#10B981",
    glow: "rgba(16, 185, 129, 0.4)",
  },
  {
    id: "VOICE_COPILOT",
    label: "Voice Copilot",
    sublabel: "Gemini Live WebRTC",
    emoji: "🎙️",
    x: 390,
    y: 255,
    color: "#F43F5E",
    glow: "rgba(244, 63, 94, 0.4)",
  },
  {
    id: "SANDBOX",
    label: "gVisor Sandbox",
    sublabel: "runsc micro-kernel",
    emoji: "📦",
    x: 660,
    y: 150,
    color: "#38BDF8",
    glow: "rgba(56, 189, 248, 0.4)",
  },
  {
    id: "SUPERVISOR_HEALER",
    label: "Supervisor Healer",
    sublabel: "3.7 Flash Thinking",
    emoji: "🩺",
    x: 930,
    y: 150,
    color: "#F59E0B",
    glow: "rgba(245, 158, 11, 0.4)",
  },
  {
    id: "CICD_DAEMON",
    label: "CI/CD Daemon",
    sublabel: "Auto-PR Engine",
    emoji: "🤖",
    x: 930,
    y: 255,
    color: "#38BDF8",
    glow: "rgba(56, 189, 248, 0.4)",
  },
];

interface EdgeConnection {
  from: AgentRole | "SANDBOX";
  to: AgentRole | "SANDBOX";
  label?: string;
  dashed?: boolean;
}

const EDGES: EdgeConnection[] = [
  // Primary flow: Architect -> Coder -> Sandbox -> Supervisor
  { from: "ARCHITECT", to: "CODER", label: "Delegates Plan" },
  { from: "CODER", to: "SANDBOX", label: "Dispatches Tool" },
  { from: "SANDBOX", to: "SUPERVISOR_HEALER", label: "Catches Error" },
  { from: "SUPERVISOR_HEALER", to: "CODER", label: "Injects Patch", dashed: true },

  // Sentinel Oversight
  { from: "FINOPS_SENTINEL", to: "ARCHITECT", dashed: true },
  { from: "FINOPS_SENTINEL", to: "CODER", label: "Velocity Audit", dashed: true },

  // Voice Diagnostics
  { from: "VOICE_COPILOT", to: "CODER", label: "DOM Sync", dashed: true },
  { from: "VOICE_COPILOT", to: "SANDBOX", dashed: true },

  // CI/CD Release
  { from: "SANDBOX", to: "CICD_DAEMON", label: "Verified Pass@1" },
  { from: "CICD_DAEMON", to: "ARCHITECT", label: "PR Merged", dashed: true },
];

export function AgentSwarmNodeMap({
  activeAgent,
  activeHandoff,
  agentStats,
  onSelectAgent,
  className,
}: AgentSwarmNodeMapProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const getNode = (id: string) => NODES.find((n) => n.id === id);

  return (
    <div
      className={cn(
        "relative rounded-xl border border-white/10 bg-[#0A0D14]/80 p-5 backdrop-blur-2xl shadow-2xl overflow-hidden select-none",
        className
      )}
    >
      {/* Background ambient lighting */}
      <div className="absolute -top-32 -left-32 w-80 h-80 bg-[#00F0FF]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -right-32 w-80 h-80 bg-[#10B981]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#8B5CF6]/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#00F0FF]" />
          </span>
          <h3 className="text-sm font-bold text-white font-mono tracking-wide uppercase flex items-center gap-2">
            Multi-Agent Swarm Topology & Active Handoff Matrix
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-zinc-400">Active Node:</span>
          <span
            className="px-2.5 py-0.5 rounded-full border text-xs font-bold font-mono transition-all animate-pulse"
            style={{
              borderColor: AGENT_METADATA_MAP[activeAgent]?.color || "#00F0FF",
              color: AGENT_METADATA_MAP[activeAgent]?.color || "#00F0FF",
              backgroundColor: AGENT_METADATA_MAP[activeAgent]?.bgGlow || "rgba(0, 240, 255, 0.1)",
            }}
          >
            {AGENT_METADATA_MAP[activeAgent]?.emoji} {AGENT_METADATA_MAP[activeAgent]?.displayName}
          </span>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox="0 0 1050 300"
          className="w-full min-w-[780px] h-[260px] text-zinc-400 font-mono"
        >
          <defs>
            {/* Arrowhead markers */}
            <marker
              id="arrow-cyan"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#00F0FF" />
            </marker>
            <marker
              id="arrow-emerald"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#10B981" />
            </marker>
            <marker
              id="arrow-amber"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#F59E0B" />
            </marker>
            <marker
              id="arrow-purple"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#8B5CF6" />
            </marker>
            <marker
              id="arrow-muted"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="rgba(255, 255, 255, 0.2)" />
            </marker>

            {/* Glowing filters */}
            <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Render Connection Edges */}
          {EDGES.map((edge, idx) => {
            const fromNode = getNode(edge.from);
            const toNode = getNode(edge.to);
            if (!fromNode || !toNode) return null;

            const isHandoffActive =
              (activeHandoff?.from === edge.from && activeHandoff?.to === edge.to) ||
              (edge.from === activeAgent && edge.to === "CODER") ||
              (edge.from === "CODER" && edge.to === "SANDBOX" && activeAgent === "CODER");

            // Curvature calculation for aesthetic PCB / circuit routing
            const dx = toNode.x - fromNode.x;
            const dy = toNode.y - fromNode.y;
            const isCurved = Math.abs(dy) > 20 && Math.abs(dx) > 20;

            let pathD = `M ${fromNode.x} ${fromNode.y} L ${toNode.x} ${toNode.y}`;
            if (isCurved) {
              const cx1 = fromNode.x + dx * 0.5;
              const cy1 = fromNode.y;
              const cx2 = fromNode.x + dx * 0.5;
              const cy2 = toNode.y;
              pathD = `M ${fromNode.x} ${fromNode.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${toNode.x} ${toNode.y}`;
            }

            return (
              <g key={`edge-${idx}`}>
                {/* Background base wire */}
                <path
                  d={pathD}
                  stroke={isHandoffActive ? "rgba(0, 240, 255, 0.6)" : "rgba(255, 255, 255, 0.1)"}
                  strokeWidth={isHandoffActive ? 2.5 : 1.2}
                  strokeDasharray={edge.dashed ? "4 4" : undefined}
                  fill="none"
                  markerEnd={isHandoffActive ? "url(#arrow-cyan)" : "url(#arrow-muted)"}
                  className="transition-all duration-300"
                />

                {/* Animated active energy particle on active handoff */}
                {isHandoffActive && (
                  <circle r="4" fill="#00F0FF" filter="url(#glow-cyan)">
                    <animateMotion path={pathD} dur="1.5s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Edge Micro Label */}
                {edge.label && (
                  <text
                    x={(fromNode.x + toNode.x) / 2}
                    y={(fromNode.y + toNode.y) / 2 - 8}
                    fill={isHandoffActive ? "#00F0FF" : "#64748B"}
                    fontSize="9"
                    textAnchor="middle"
                    className="font-mono font-semibold select-none"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Render Nodes */}
          {NODES.map((node) => {
            const isCurrentActive = activeAgent === node.id;
            const isSelected = selectedNode === node.id;
            const stats = agentStats && node.id in agentStats ? (agentStats as any)[node.id] : null;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => {
                  setSelectedNode(node.id);
                  if (node.id !== "SANDBOX" && onSelectAgent) {
                    onSelectAgent(node.id as AgentRole);
                  }
                }}
                className="cursor-pointer group"
              >
                {/* Pulsing ring on active node */}
                {isCurrentActive && (
                  <>
                    <circle
                      r="42"
                      fill="none"
                      stroke={node.color}
                      strokeWidth="1.5"
                      opacity="0.3"
                      className="animate-ping-slow"
                    />
                    <circle
                      r="36"
                      fill="none"
                      stroke={node.color}
                      strokeWidth="2"
                      opacity="0.6"
                      className="animate-pulse"
                    />
                  </>
                )}

                {/* Node Body Card Box */}
                <rect
                  x="-68"
                  y="-26"
                  width="136"
                  height="52"
                  rx="12"
                  fill={isCurrentActive ? "#121722" : "#0A0D14"}
                  stroke={isCurrentActive ? node.color : isSelected ? "#FFFFFF" : "rgba(255,255,255,0.12)"}
                  strokeWidth={isCurrentActive ? 2 : 1}
                  className="transition-all duration-300 group-hover:stroke-white/50"
                  style={{
                    filter: isCurrentActive ? `drop-shadow(0 0 12px ${node.glow})` : undefined,
                  }}
                />

                {/* Emoji Avatar */}
                <text x="-48" y="6" fontSize="18" textAnchor="middle" className="select-none">
                  {node.emoji}
                </text>

                {/* Node Title */}
                <text
                  x="-32"
                  y="-4"
                  fill={isCurrentActive ? "#FFFFFF" : "#E2E8F0"}
                  fontSize="11"
                  fontWeight="bold"
                  textAnchor="start"
                  className="font-mono select-none"
                >
                  {node.label}
                </text>

                {/* Subtitle / Model tier */}
                <text
                  x="-32"
                  y="12"
                  fill={isCurrentActive ? node.color : "#94A3B8"}
                  fontSize="9"
                  textAnchor="start"
                  className="font-mono select-none"
                >
                  {node.sublabel}
                </text>

                {/* Status Dot */}
                <circle
                  cx="54"
                  cy="-14"
                  r="3.5"
                  fill={isCurrentActive ? node.color : "rgba(255,255,255,0.2)"}
                  className={isCurrentActive ? "animate-pulse" : ""}
                />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Node Mini Summary / Stats Strip */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-6 gap-2 border-t border-white/10 pt-3">
        {NODES.filter((n) => n.id !== "SANDBOX").map((node) => {
          const isCurrent = activeAgent === node.id;
          const stats = agentStats && node.id in agentStats ? (agentStats as any)[node.id] : null;

          return (
            <div
              key={`stat-${node.id}`}
              onClick={() => {
                if (onSelectAgent) onSelectAgent(node.id as AgentRole);
              }}
              className={cn(
                "p-2 rounded-lg border text-center transition-all cursor-pointer font-mono",
                isCurrent
                  ? "bg-white/[0.06] border-white/30 shadow-lg"
                  : "bg-white/[0.02] border-white/5 hover:border-white/15"
              )}
            >
              <div className="text-[10px] text-zinc-400 truncate flex items-center justify-center gap-1">
                <span>{node.emoji}</span>
                <span className="font-semibold">{node.label}</span>
              </div>
              <div
                className="text-xs font-bold mt-0.5"
                style={{ color: isCurrent ? node.color : "#FFFFFF" }}
              >
                {stats ? `${stats.turnsCompleted} turns` : isCurrent ? "ACTIVE" : "IDLE"}
              </div>
              {stats && (
                <div className="text-[9px] text-zinc-500 truncate">{formatUsd(stats.costUsd)}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
