"use client";

import React, { use, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Terminal,
  Activity,
  DollarSign,
  Shield,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
  Layers,
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TrajectoryInspectorPage({ params }: PageProps) {
  const { id } = use(params);
  const [selectedTurn, setSelectedTurn] = useState<number>(4);

  // Curated turn-by-turn trace for the inspected trajectory
  const turns = [
    {
      turn: 1,
      role: "ARCHITECT (Gemini 2.5 Pro)",
      action: "explore_ast",
      costUsd: 0.08,
      tokens: 4200,
      latencyMs: 1420,
      status: "PASS",
      fsmState: "REASONING_PLANNER",
      log: `[PLANNER]: Analyzing repository AST for django__django-11099.
[PLANNER]: Target file identified: django/core/validators.py (Lines 42-65).
[PLANNER]: Root Cause: Trailing newline in ASCIIUsernameValidator regex pattern causes regex bypass.
[PLANNER]: 3-Step Remediation Plan formulated. Delegating execution to CODER_AGENT.`,
    },
    {
      turn: 2,
      role: "CODER (Gemini 3.5 Flash)",
      action: "edit_hunk",
      costUsd: 0.03,
      tokens: 1850,
      latencyMs: 480,
      status: "PASS",
      fsmState: "TOOL_DISPATCH_CODER",
      log: `[CODER]: Applying unified diff hunk to django/core/validators.py:
--- a/django/core/validators.py
+++ b/django/core/validators.py
@@ -47,3 +47,3 @@ class ASCIIUsernameValidator(validators.RegexValidator):
-    regex = r'^[\\w.@+-]+\\Z'
+    regex = r'\\A[\\w.@+-]+\\Z'
[CODER]: Diff applied cleanly to git tree hash: e8f92a10.`,
    },
    {
      turn: 3,
      role: "CODER (Gemini 3.5 Flash)",
      action: "run_pytest",
      costUsd: 0.04,
      tokens: 2100,
      latencyMs: 820,
      status: "HEALED",
      fsmState: "EVAL_ASSERTION",
      isHealed: true,
      log: `[CODER]: Executing tool: runPytest('tests/test_validators.py')...
[ERROR]: Schema Argument Mismatch: 'test_path' expected string, got dict.
[SUPERVISOR_AST_HEALER (Gemini 3.7 Flash Thinking)]:
>>> Intercepted tool schema offset failure.
>>> Synthesizing in-memory dynamic parameter adapter:
    def adapt_pytest_args(raw): return {"test_path": raw.get("path", "tests/test_validators.py")}
>>> Adapter injected into sandbox runtime. Retrying turn...
[CODER]: Executing repaired runPytest invocation...
>>> Pytest Result: 13 passed, 1 failed (AssertionError: newline validation regression).`,
    },
    {
      turn: 4,
      role: "CODER (Gemini 3.5 Flash)",
      action: "edit_hunk & run_pytest",
      costUsd: 0.05,
      tokens: 2400,
      latencyMs: 950,
      status: "PASS",
      fsmState: "COMPLETE",
      log: `[CODER]: Adjusting UnicodeUsernameValidator regex pattern.
[CODER]: Re-running pytest suite: pytest tests/test_validators.py
============================= 14 passed in 0.42s ==============================
[GIT_SAGA]: All test assertions passed with zero regressions.
[SENTINEL]: Total Trajectory Cost: $0.20 (Under $2.00 ceiling).
[STATE]: Trajectory marked COMPLETE with exit code 0.`,
    },
  ];

  const currentTurnData = turns[selectedTurn - 1] || turns[0];
  const totalCost = turns.reduce((acc, t) => acc + t.costUsd, 0);
  const totalTokens = turns.reduce((acc, t) => acc + t.tokens, 0);

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/models"
            className="flex items-center gap-2 text-xs font-mono text-gray-400 hover:text-[#00F0FF] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Models
          </Link>

          <Badge variant="amber" size="sm" dot>
            Demo Fixture Trace (Illustrative)
          </Badge>
        </div>

        {/* Header Summary */}
        <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-gray-400">Trajectory ID:</span>
                <span className="font-mono text-xs font-bold text-[#00F0FF]">{id}</span>
                <span className="text-gray-600">•</span>
                <span className="text-xs font-mono text-gray-400">Suite: swe_bench_verified</span>
              </div>
              <h1 className="text-2xl font-extrabold text-white">
                django__django-11099 (ASCIIUsernameValidator Fix)
              </h1>
            </div>

            {/* Metrics Pills */}
            <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
              <div className="rounded-lg bg-black/40 border border-white/5 px-3 py-2">
                <span className="text-gray-500">Total Spend:</span>{" "}
                <span className="font-bold text-[#10B981]">${totalCost.toFixed(2)}</span>
              </div>
              <div className="rounded-lg bg-black/40 border border-white/5 px-3 py-2">
                <span className="text-gray-500">Total Turns:</span>{" "}
                <span className="font-bold text-white">{turns.length} turns</span>
              </div>
              <div className="rounded-lg bg-black/40 border border-white/5 px-3 py-2">
                <span className="text-gray-500">Total Tokens:</span>{" "}
                <span className="font-bold text-purple-400">{totalTokens.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Turn Selector Strip */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {turns.map((t) => (
            <button
              key={t.turn}
              onClick={() => setSelectedTurn(t.turn)}
              className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-mono font-bold transition-all ${
                selectedTurn === t.turn
                  ? "border-[#00F0FF]/50 bg-[#00F0FF]/15 text-[#00F0FF] shadow-glass-cyan"
                  : "border-white/10 bg-[#121722]/60 text-gray-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span>Turn {t.turn}</span>
              <span className="text-[10px] text-gray-400">({t.action})</span>
              {t.isHealed && <Sparkles className="h-3 w-3 text-amber-400" />}
            </button>
          ))}
        </div>

        {/* Split View: Terminal Logs (Left) vs Turn Metadata (Right) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Virtual Terminal Log (2 Cols) */}
          <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-black/90 p-6 font-mono text-xs backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
              <div className="flex items-center gap-2 text-gray-400">
                <Terminal className="h-4 w-4 text-[#00F0FF]" />
                <span>gVisor Sandbox Execution Output (Turn {selectedTurn})</span>
              </div>
              <Badge variant={currentTurnData.isHealed ? "amber" : "cyan"} size="sm">
                {currentTurnData.fsmState}
              </Badge>
            </div>

            <pre className="overflow-x-auto text-gray-300 leading-relaxed whitespace-pre-wrap">
              {currentTurnData.log}
            </pre>
          </div>

          {/* Turn Metadata Column (1 Col) */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-white/10 bg-[#121722]/80 p-6 backdrop-blur-xl space-y-4 font-mono text-xs">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Turn {selectedTurn} Telemetry</h3>

              <div className="space-y-3 divide-y divide-white/5">
                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">Executing Agent:</span>
                  <span className="font-bold text-[#00F0FF]">{currentTurnData.role}</span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">Action Type:</span>
                  <span className="text-white">{currentTurnData.action}</span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">Turn Token Cost:</span>
                  <span className="font-bold text-[#10B981]">${currentTurnData.costUsd.toFixed(2)}</span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">Tokens Consumed:</span>
                  <span className="text-purple-400">{currentTurnData.tokens.toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">Turn Latency:</span>
                  <span className="text-gray-200">{currentTurnData.latencyMs} ms</span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-gray-400">FSM State:</span>
                  <Badge variant="cyan" size="sm">
                    {currentTurnData.fsmState}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Autonomous Self-Healing Card */}
            {currentTurnData.isHealed && (
              <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5 backdrop-blur-xl text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-400">
                  <Sparkles className="h-4 w-4" />
                  Supervisor AST Healer Intervened
                </div>
                <p className="text-gray-300">
                  An argument schema mismatch was intercepted during tool dispatch. The supervisor dynamically synthesized and injected an in-memory adapter wrapper without stopping the run.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
