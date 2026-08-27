"use client";

import React from "react";
import { Terminal, Check, AlertCircle, Copy } from "lucide-react";
import { TrajectoryTurnEvent } from "@/lib/types";

interface SandboxTerminalPaneProps {
  currentTurn?: TrajectoryTurnEvent | null;
  logs?: string[];
}

export function SandboxTerminalPane({ currentTurn, logs = [] }: SandboxTerminalPaneProps) {
  const stdout = currentTurn?.sandbox_stdout || "";
  const stderr = currentTurn?.sandbox_stderr || "";
  const toolName = currentTurn?.tool_call_name;
  const toolArgs = currentTurn?.tool_call_payload;

  return (
    <div className="rounded-xl border border-white/10 bg-black/80 font-mono text-xs shadow-2xl flex flex-col h-[380px] overflow-hidden">
      {/* Terminal Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-obsidian-900 border-b border-white/10 text-zinc-400">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <span className="text-[11px] text-zinc-300 font-semibold ml-2 flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-[#00F0FF]" />
            gVisor Sandbox Terminal (runsc)
          </span>
        </div>

        {currentTurn && (
          <div className="flex items-center gap-2 text-[10px]">
            <span>Exit Code:</span>
            <span
              className={`font-bold px-1.5 py-0.2 rounded ${
                currentTurn.sandbox_exit_code === 0
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "bg-rose-500/20 text-rose-300"
              }`}
            >
              {currentTurn.sandbox_exit_code}
            </span>
          </div>
        )}
      </div>

      {/* Terminal Content */}
      <div className="flex-1 p-4 overflow-y-auto space-y-2 text-zinc-300 selection:bg-[#00F0FF]/30">
        <div className="text-zinc-500 text-[11px]">
          [sandbox-init] Mounted ephemeral tmpfs workspace /tmp/benchpress_ws/
        </div>

        {toolName && (
          <div className="text-emerald-400">
            $ <span className="text-white font-bold">{toolName}</span>
            {toolArgs && <span className="text-zinc-400"> {JSON.stringify(toolArgs)}</span>}
          </div>
        )}

        {/* Diff rendering */}
        {toolName === "editHunk" && toolArgs && (
          <div className="p-2 rounded bg-black/60 border border-white/5 space-y-0.5 text-[11px]">
            <div className="text-zinc-500">--- {toolArgs.path} (original)</div>
            <div className="text-zinc-500">+++ {toolArgs.path} (repaired)</div>
            <div className="text-rose-400 bg-rose-950/20 px-1">- {toolArgs.target_content}</div>
            <div className="text-emerald-400 bg-emerald-950/20 px-1">+ {toolArgs.replacement_content}</div>
          </div>
        )}

        {stdout && (
          <div className="text-zinc-200 whitespace-pre-wrap leading-relaxed">
            {stdout}
          </div>
        )}

        {stderr && (
          <div className="text-rose-400 whitespace-pre-wrap leading-relaxed bg-rose-950/20 p-2 rounded border border-rose-500/20">
            {stderr}
          </div>
        )}

        {currentTurn?.ast_healed && (
          <div className="text-amber-300 bg-amber-950/20 p-2 rounded border border-amber-500/20 text-[11px]">
            ⚡ [AST Supervisor]: Injected runtime tool repair wrapper adapter.
          </div>
        )}

        {/* Blinking Prompt Cursor */}
        <div className="flex items-center gap-1 text-[#00F0FF] pt-2">
          <span>benchpress-agent@sandbox:~$</span>
          <span className="w-2 h-3.5 bg-[#00F0FF] animate-pulse inline-block" />
        </div>
      </div>
    </div>
  );
}
