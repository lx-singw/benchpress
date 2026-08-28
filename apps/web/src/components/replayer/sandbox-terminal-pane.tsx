"use client";

import React, { useState } from "react";
import { Terminal, Check, AlertCircle, Copy, Code2, Sparkles, GitBranch } from "lucide-react";
import { TrajectoryTurnEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SandboxTerminalPaneProps {
  currentTurn?: TrajectoryTurnEvent | null;
  logs?: string[];
  highlightedLine?: number | null;
  highlightedFile?: string | null;
  activeTool?: string | null;
  className?: string;
}

export function SandboxTerminalPane({
  currentTurn,
  logs = [],
  highlightedLine,
  highlightedFile,
  activeTool,
  className,
}: SandboxTerminalPaneProps) {
  const [copied, setCopied] = useState(false);

  const stdout = currentTurn?.sandbox_stdout || "";
  const stderr = currentTurn?.sandbox_stderr || "";
  const toolName = activeTool || currentTurn?.tool_call_name;
  const toolArgs = currentTurn?.tool_call_payload;

  const handleCopyLogs = () => {
    const textToCopy = `[gVisor Sandbox Log]\nTool: ${toolName || "N/A"}\nArgs: ${JSON.stringify(
      toolArgs || {}
    )}\nStdout: ${stdout}\nStderr: ${stderr}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-white/10 bg-black/90 font-mono text-xs shadow-2xl flex flex-col h-[580px] overflow-hidden",
        className
      )}
    >
      {/* Terminal Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#0A0D14] border-b border-white/10 text-zinc-400">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <span className="text-[11px] text-zinc-200 font-bold ml-2 flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-[#00F0FF]" />
            gVisor Sandbox Terminal (runsc on AMD SEV-SNP)
          </span>
        </div>

        <div className="flex items-center gap-3 text-[10px]">
          {currentTurn?.git_tree_hash && (
            <span className="hidden sm:flex items-center gap-1 text-purple-300 bg-purple-950/30 px-2 py-0.5 rounded border border-purple-500/20">
              <GitBranch className="w-3 h-3" />
              <span>{currentTurn.git_tree_hash.substring(0, 7)}</span>
            </span>
          )}

          {currentTurn && (
            <div className="flex items-center gap-1.5">
              <span className="text-zinc-500">Exit:</span>
              <span
                className={cn(
                  "font-bold px-1.5 py-0.5 rounded",
                  currentTurn.sandbox_exit_code === 0
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "bg-rose-500/20 text-rose-300"
                )}
              >
                {currentTurn.sandbox_exit_code}
              </span>
            </div>
          )}

          <button
            onClick={handleCopyLogs}
            className="p-1 rounded hover:bg-white/10 text-zinc-400 hover:text-white transition"
            title="Copy Terminal Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 p-4 overflow-y-auto space-y-2.5 text-zinc-300 selection:bg-[#00F0FF]/30 leading-relaxed">
        <div className="text-zinc-500 text-[11px] border-b border-white/5 pb-2">
          [sandbox-init] Mounted ephemeral tmpfs workspace /tmp/benchpress_ws/ (2GB RAM ceiling)
          <br />
          [seccomp-bpf] Intercepting 300+ Linux syscalls in user-space Go (Sentry kernel)
        </div>

        {/* Highlight Focus Banner if active */}
        {highlightedFile && (
          <div className="p-2.5 rounded-lg bg-[#00F0FF]/10 border border-[#00F0FF]/30 text-cyan-300 text-[11px] flex items-center justify-between animate-pulse">
            <span className="flex items-center gap-1.5 font-bold">
              <Code2 className="w-3.5 h-3.5" /> DOM Sync Focus: {highlightedFile}
              {highlightedLine && ` (Line ${highlightedLine})`}
            </span>
            <span className="text-[10px] text-cyan-400/80 font-normal">Active Diff Synced</span>
          </div>
        )}

        {/* Tool Call Invocation */}
        {toolName && (
          <div className="text-emerald-400 pt-1">
            <span className="text-zinc-500">benchpress-agent@gvisor:~$</span>{" "}
            <span className="text-white font-bold">{toolName}</span>
            {toolArgs && (
              <span className="text-zinc-400 text-[11px]"> {JSON.stringify(toolArgs, null, 2)}</span>
            )}
          </div>
        )}

        {/* Diff rendering */}
        {toolName === "editHunk" && toolArgs && (
          <div className="p-3 rounded-lg bg-black/80 border border-white/10 space-y-1 text-[11px] font-mono">
            <div className="flex justify-between text-zinc-400 text-[10px] border-b border-white/5 pb-1 mb-1">
              <span>--- {toolArgs.path} (original)</span>
              <span>+++ {toolArgs.path} (healed)</span>
            </div>
            {toolArgs.target_content && (
              <div className="text-rose-400 bg-rose-950/30 px-2 py-0.5 rounded border border-rose-500/20">
                - {toolArgs.target_content}
              </div>
            )}
            {toolArgs.replacement_content && (
              <div className="text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/20">
                + {toolArgs.replacement_content}
              </div>
            )}
          </div>
        )}

        {/* Stdout Stream */}
        {stdout && (
          <div className="text-zinc-200 whitespace-pre-wrap leading-relaxed bg-[#121722]/50 p-3 rounded-lg border border-white/5">
            {stdout}
          </div>
        )}

        {/* Stderr Stream */}
        {stderr && (
          <div className="text-rose-400 whitespace-pre-wrap leading-relaxed bg-rose-950/25 p-3 rounded-lg border border-rose-500/30">
            {stderr}
          </div>
        )}

        {/* AST Supervisor Healing Injection Alert */}
        {currentTurn?.ast_healed && (
          <div className="text-amber-300 bg-amber-950/30 p-2.5 rounded-lg border border-amber-500/40 text-[11px] flex items-center gap-2 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold">⚡ [AST Supervisor Injection]:</span> Auto-repaired non-standard
              tool parameter signature in 142ms. Clean diff applied with 0 syntax errors.
            </div>
          </div>
        )}

        {/* Blinking Prompt Cursor */}
        <div className="flex items-center gap-1.5 text-[#00F0FF] pt-2">
          <span>benchpress-agent@sandbox:~$</span>
          <span className="w-2 h-4 bg-[#00F0FF] animate-pulse inline-block" />
        </div>
      </div>
    </div>
  );
}
