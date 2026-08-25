"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  DollarSign,
  Flame,
  GitCommit,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  Wrench,
  Zap,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatPercent, formatUsd } from "@/lib/utils";
import { FsmState, TrajectoryStatus } from "@/lib/types";

interface StepRecord {
  turn: number;
  state: FsmState;
  model: string;
  cost: number;
  cumulativeCost: number;
  latencyMs: number;
  astHealed: boolean;
  action: string;
}

const INITIAL_STEPS: StepRecord[] = [
  {
    turn: 1,
    state: FsmState.INIT_ENVIRONMENT,
    model: "gemini-2.5-pro",
    cost: 0.005,
    cumulativeCost: 0.005,
    latencyMs: 340,
    astHealed: false,
    action: "Mounted gVisor runsc sandbox & cloned repo fixture (SWE-bench/django-12858)",
  },
  {
    turn: 2,
    state: FsmState.PROMPT_PLANNER,
    model: "gemini-2.5-pro",
    cost: 0.038,
    cumulativeCost: 0.043,
    latencyMs: 1820,
    astHealed: false,
    action: "Planner formulated 3-phase execution plan for model ordering constraint bug",
  },
  {
    turn: 3,
    state: FsmState.VALIDATE_AST,
    model: "gemini-2.5-flash",
    cost: 0.012,
    cumulativeCost: 0.055,
    latencyMs: 650,
    astHealed: true,
    action: "Autonomous AST Healer auto-corrected tool schema parameter mismatch in edit_file()",
  },
  {
    turn: 4,
    state: FsmState.EXECUTE_SANDBOX,
    model: "gemini-2.5-flash",
    cost: 0.018,
    cumulativeCost: 0.073,
    latencyMs: 2400,
    astHealed: false,
    action: "Executed pytest tests/ordering/tests.py in isolated sandbox (1 failed -> 1 passed)",
  },
  {
    turn: 5,
    state: FsmState.FINOPS_SENTINEL,
    model: "sentinel-markov-v1",
    cost: 0.001,
    cumulativeCost: 0.074,
    latencyMs: 120,
    astHealed: false,
    action: "Markov Sentinel evaluated velocity: Projected total cost $0.21 (< $2.00 cap) -> CONTINUE",
  },
];

export default function LiveRunnerPage() {
  const [modelId, setModelId] = useState<string>("gemini-2.5-pro");
  const [taskSuite, setTaskSuite] = useState<string>("SWE_BENCH_VERIFIED");
  const [taskId, setTaskId] = useState<string>("django__django-12858");
  const [budgetLimit, setBudgetLimit] = useState<number>(2.0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [steps, setSteps] = useState<StepRecord[]>(INITIAL_STEPS);

  const handleLaunch = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
    }, 2500);
  };

  const totalCost = steps.length > 0 ? steps[steps.length - 1].cumulativeCost : 0;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header */}
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="emerald" dot size="sm">
              REAL-TIME FSM RUNNER
            </Badge>
            <span className="text-xs text-gray-500 font-mono">13-State Deterministic Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            Live Trajectory Execution & Token Waterfall
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Inspect autonomous agent execution steps, AST self-healing intercepts, and FinOps budget guardrails in real time.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="cyan" size="md">
            gVisor Sandbox: HEALTHY
          </Badge>
        </div>
      </div>

      {/* Grid: Trajectory Dispatcher Form + Live Stats */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Trajectory Config Form */}
        <GlassCard className="p-6 lg:col-span-1" glow="none">
          <div className="flex items-center gap-2 mb-4">
            <Terminal className="h-5 w-5 text-[#00F0FF]" />
            <h3 className="font-semibold text-white">Dispatch Trajectory</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-gray-400 mb-1.5 uppercase">
                Model Router Target
              </label>
              <select
                value={modelId}
                onChange={(e) => setModelId(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#0A0D14] px-3 py-2 text-xs font-mono text-white focus:border-[#00F0FF] focus:outline-none"
              >
                <option value="gemini-2.5-pro">Gemini 2.5 Pro (Planner / Complex Coder)</option>
                <option value="gemini-2.5-flash">Gemini 2.5 Flash (Fast Execution)</option>
                <option value="claude-3-7-sonnet">Claude 3.7 Sonnet (Thinking)</option>
                <option value="o3-mini">o3-mini (High Reasoning)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-gray-400 mb-1.5 uppercase">
                Benchmark Task Suite
              </label>
              <select
                value={taskSuite}
                onChange={(e) => setTaskSuite(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#0A0D14] px-3 py-2 text-xs font-mono text-white focus:border-[#00F0FF] focus:outline-none"
              >
                <option value="SWE_BENCH_VERIFIED">SWE-bench Verified (Python Bugs)</option>
                <option value="HUMANEVAL_XL">HumanEval-XL (Multi-Lingual)</option>
                <option value="CYBENCH">Cybench (Cybersecurity CTFs)</option>
                <option value="GAIA">GAIA (Multimodal General Assistant)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-gray-400 mb-1.5 uppercase">
                Task ID / Fixture
              </label>
              <input
                type="text"
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#0A0D14] px-3 py-2 text-xs font-mono text-white focus:border-[#00F0FF] focus:outline-none"
              />
            </div>

            <div>
              <div className="flex items-center justify-between text-xs font-mono text-gray-400 mb-1.5">
                <span className="uppercase">FinOps Budget Cap</span>
                <span className="text-[#00F0FF] font-bold">{formatUsd(budgetLimit)}</span>
              </div>
              <input
                type="range"
                min="0.25"
                max="5.00"
                step="0.25"
                value={budgetLimit}
                onChange={(e) => setBudgetLimit(parseFloat(e.target.value))}
                className="w-full accent-[#00F0FF]"
              />
            </div>

            <button
              onClick={handleLaunch}
              disabled={isRunning}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#00F0FF] to-[#10B981] py-2.5 text-xs font-semibold uppercase tracking-wider text-[#0A0D14] hover:opacity-95 disabled:opacity-50 transition-all shadow-glass-cyan"
            >
              {isRunning ? (
                <>
                  <RotateCcw className="h-4 w-4 animate-spin" />
                  Streaming Trajectory...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Enqueue Trajectory Task
                </>
              )}
            </button>
          </div>

          <div className="mt-6 rounded-lg border border-white/5 bg-[#0A0D14]/60 p-3 text-[11px] font-mono text-gray-400 space-y-1">
            <div className="flex justify-between">
              <span>Cloud Tasks Queue:</span>
              <span className="text-gray-200">trajectory-execution-queue</span>
            </div>
            <div className="flex justify-between">
              <span>Isolation Engine:</span>
              <span className="text-[#10B981]">gVisor runsc</span>
            </div>
            <div className="flex justify-between">
              <span>Telemetry Sink:</span>
              <span className="text-[#00F0FF]">BigQuery Storage Write API</span>
            </div>
          </div>
        </GlassCard>

        {/* Live Waterfall & Timeline (2 Cols on Desktop) */}
        <GlassCard className="p-6 lg:col-span-2 flex flex-col justify-between" glow="none">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-[#10B981]" />
                <h3 className="font-semibold text-white">Trajectory Waterfall & Event Timeline</h3>
              </div>
              <Badge variant="cyan" size="sm">
                Active Trajectory: traj-8f4b2a9c
              </Badge>
            </div>

            {/* Trajectory Header Summary */}
            <div className="mb-6 grid grid-cols-3 gap-3 rounded-lg border border-white/10 bg-[#0A0D14]/80 p-3 text-xs font-mono">
              <div>
                <div className="text-gray-500 uppercase text-[10px]">Accumulated Cost</div>
                <div className="text-base font-bold text-[#00F0FF]">{formatUsd(totalCost)}</div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-[10px]">Budget Utilization</div>
                <div className="text-base font-bold text-[#10B981]">
                  {formatPercent((totalCost / budgetLimit) * 100)}
                </div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-[10px]">Completed Turns</div>
                <div className="text-base font-bold text-white">{steps.length} / 20</div>
              </div>
            </div>

            {/* Waterfall Step List */}
            <div className="space-y-3">
              {steps.map((step) => (
                <div
                  key={step.turn}
                  className="rounded-lg border border-white/5 bg-[#121722]/60 p-3 hover:border-white/20 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5 text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-[#0A0D14] px-1.5 py-0.5 font-bold text-[#00F0FF]">
                        TURN {step.turn}
                      </span>
                      <Badge variant="neutral" size="sm">
                        {step.state}
                      </Badge>
                      {step.astHealed && (
                        <Badge variant="amber" size="sm" dot>
                          AST Auto-Healed
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-gray-400">
                      <span>{step.latencyMs}ms</span>
                      <span className="text-[#00F0FF]">{formatUsd(step.cost)}</span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-300 font-sans">{step.action}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4 text-xs font-mono text-gray-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[#10B981]" />
              <span>FinOps Velocity Guardrail: Active</span>
            </div>
            <div className="flex items-center gap-2">
              <GitCommit className="h-4 w-4 text-purple-400" />
              <span>Git Saga Snapshots: 4 captured</span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
