/**
 * Multi-Agent Swarm Protocols & Typed Communication Schemas
 * For Benchpress Interactive Multi-Agent Swarm Visualizer
 */

export type AgentRole =
  | "ARCHITECT"         // Gemini 2.5 Pro: Plan synthesis & AST analysis
  | "CODER"             // Gemini 3.5 Flash: File edits & bash execution
  | "SUPERVISOR_HEALER" // Gemini 3.7 Flash Thinking: Schema adaptation & parameter patching
  | "FINOPS_SENTINEL"   // Markov Chain: Token velocity & budget ceiling enforcement
  | "VOICE_COPILOT"     // Gemini Live WebRTC: Real-time spoken diagnostics
  | "CICD_DAEMON";      // Background PR Creator: Git branch & PR generation

export interface AgentMeta {
  role: AgentRole;
  displayName: string;
  shortName: string;
  emoji: string;
  model: string;
  color: string;
  glowColor: string;
  borderGlow: string;
  bgGlow: string;
  textClass: string;
  badgeBorderClass: string;
  badgeBgClass: string;
  badgeTextClass: string;
  badgeGlowClass: string;
  description: string;
  responsibility: string;
}

export type SwarmActionType =
  | "PLAN"
  | "TOOL_CALL"
  | "TOOL_RESULT"
  | "HEAL_PATCH"
  | "SENTINEL_AUDIT"
  | "VOICE_DIAGNOSTIC"
  | "PR_CREATED";

export interface SwarmCodeDiff {
  path: string;
  target_content?: string;
  replacement_content?: string;
  lines?: string;
  diffHunk?: string;
}

export interface SwarmMessageEnvelope {
  id: string;
  turnNumber: number;
  timestamp: string;
  fromAgent: AgentRole;
  toAgent: AgentRole | "SANDBOX" | "ALL" | "DEVELOPER";
  actionType: SwarmActionType;
  content: string;
  codeDiff?: SwarmCodeDiff;
  tokenCostUsd: number;
  tokensIncurred: number;
  isSelfHealingEvent?: boolean;
  targetLine?: number;
  targetFile?: string;
  metadata?: Record<string, any>;
}

export interface SwarmHandoffNode {
  role: AgentRole;
  isActive: boolean;
  isPulsing: boolean;
  status: "IDLE" | "ACTIVE" | "THINKING" | "INTERCEPTING" | "COMPLETE";
  turnsCompleted: number;
  tokensConsumed: number;
  costAccumulatedUsd: number;
}

export interface SwarmMetrics {
  totalTurns: number;
  totalCostUsd: number;
  cprUsd: number;
  tokenVelocityKps: number;
  activeAgent: AgentRole;
  selfHealingCount: number;
  passAt1: boolean;
  bloatRatioPct: number;
  status: "INITIALIZING" | "RUNNING" | "PAUSED" | "COMPLETE" | "HALTED";
}

export const AGENT_METADATA_MAP: Record<AgentRole, AgentMeta> = {
  ARCHITECT: {
    role: "ARCHITECT",
    displayName: "Architect Agent",
    shortName: "Architect",
    emoji: "🧠",
    model: "Gemini 2.5 Pro",
    color: "#00F0FF",
    glowColor: "rgba(0, 240, 255, 0.35)",
    borderGlow: "border-[#00F0FF]/40",
    bgGlow: "bg-[#00F0FF]/10",
    textClass: "text-[#00F0FF]",
    badgeBorderClass: "border-cyan-500/40",
    badgeBgClass: "bg-cyan-950/40",
    badgeTextClass: "text-cyan-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(0,240,255,0.25)]",
    description: "High-order reasoning, AST dependency graph parsing & multi-step execution plan synthesis.",
    responsibility: "Analyzes problem statement, inspects repository AST, formulates ground-truth hypotheses.",
  },
  CODER: {
    role: "CODER",
    displayName: "Coder Agent",
    shortName: "Coder",
    emoji: "⚡",
    model: "Gemini 3.5 Flash",
    color: "#10B981",
    glowColor: "rgba(16, 185, 129, 0.35)",
    borderGlow: "border-[#10B981]/40",
    bgGlow: "bg-[#10B981]/10",
    textClass: "text-[#10B981]",
    badgeBorderClass: "border-emerald-500/40",
    badgeBgClass: "bg-emerald-950/40",
    badgeTextClass: "text-emerald-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(16,185,129,0.25)]",
    description: "Rapid tactical file modifications, hunk edits, and terminal command dispatch.",
    responsibility: "Executes precise code diffs, runs test fixtures, and queries sandbox terminal.",
  },
  SUPERVISOR_HEALER: {
    role: "SUPERVISOR_HEALER",
    displayName: "Supervisor Healer",
    shortName: "Supervisor",
    emoji: "🩺",
    model: "Gemini 3.7 Flash Thinking",
    color: "#F59E0B",
    glowColor: "rgba(245, 158, 11, 0.35)",
    borderGlow: "border-[#F59E0B]/40",
    bgGlow: "bg-[#F59E0B]/10",
    textClass: "text-[#F59E0B]",
    badgeBorderClass: "border-amber-500/40",
    badgeBgClass: "bg-amber-950/40",
    badgeTextClass: "text-amber-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(245,158,11,0.25)]",
    description: "Autonomous AST error interception, runtime wrapper synthesis, and schema patching.",
    responsibility: "Intercepts schema mismatches, repairs broken tool arguments, eliminates looping pathologies.",
  },
  FINOPS_SENTINEL: {
    role: "FINOPS_SENTINEL",
    displayName: "FinOps Sentinel",
    shortName: "Sentinel",
    emoji: "🛡️",
    model: "Markov Chain Governor",
    color: "#8B5CF6",
    glowColor: "rgba(139, 92, 246, 0.35)",
    borderGlow: "border-[#8B5CF6]/40",
    bgGlow: "bg-[#8B5CF6]/10",
    textClass: "text-[#8B5CF6]",
    badgeBorderClass: "border-purple-500/40",
    badgeBgClass: "bg-purple-950/40",
    badgeTextClass: "text-purple-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(139,92,246,0.25)]",
    description: "Turn-5 Markov token velocity forecasting, dynamic tier downgrading, and budget enforcement.",
    responsibility: "Forecasts trajectory cost, prevents runaway loops, enforces $2.00 hard budget ceiling.",
  },
  VOICE_COPILOT: {
    role: "VOICE_COPILOT",
    displayName: "Voice Copilot",
    shortName: "Voice Live",
    emoji: "🎙️",
    model: "Gemini Live WebRTC",
    color: "#F43F5E",
    glowColor: "rgba(244, 63, 94, 0.35)",
    borderGlow: "border-[#F43F5E]/40",
    bgGlow: "bg-[#F43F5E]/10",
    textClass: "text-[#F43F5E]",
    badgeBorderClass: "border-rose-500/40",
    badgeBgClass: "bg-rose-950/40",
    badgeTextClass: "text-rose-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(244,63,94,0.25)]",
    description: "Sub-200ms duplex audio streaming, spoken diagnostics & real-time DOM synchronization.",
    responsibility: "Provides spoken explanations, highlights code diff lines, syncs developer UI in real time.",
  },
  CICD_DAEMON: {
    role: "CICD_DAEMON",
    displayName: "CI/CD Daemon",
    shortName: "CI/CD Bot",
    emoji: "🤖",
    model: "Autonomous PR Engine",
    color: "#38BDF8",
    glowColor: "rgba(56, 189, 248, 0.35)",
    borderGlow: "border-[#38BDF8]/40",
    bgGlow: "bg-[#38BDF8]/10",
    textClass: "text-[#38BDF8]",
    badgeBorderClass: "border-sky-500/40",
    badgeBgClass: "bg-sky-950/40",
    badgeTextClass: "text-sky-400",
    badgeGlowClass: "shadow-[0_0_15px_rgba(56,189,248,0.25)]",
    description: "Automated branch creation, commit signing via KMS GPG & [BENCHPRESS-AUTO] PR generation.",
    responsibility: "Packages verified patches, attaches FinOps CPR audit reports, and opens pull requests.",
  },
};
