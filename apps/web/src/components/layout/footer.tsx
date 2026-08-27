"use client";

import React from "react";
import { Sparkles, Shield, Github, Activity, Terminal } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-white/10 bg-black/60 backdrop-blur-xl py-12 text-zinc-400 font-mono text-xs">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white tracking-wider">BENCHPRESS</span>
            <span className="text-zinc-600">|</span>
            <span className="text-zinc-400">The Economic Intelligence Platform for AI Agents</span>
          </div>
          <p className="text-zinc-500 font-sans text-xs max-w-md">
            The Enterprise Economic & Trajectory Intelligence Platform for Autonomous AI Agents. Continuous SWE-bench evaluation on Cloud Run Gen2 with gVisor sandboxing and BigQuery analytics.
          </p>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-[11px] text-zinc-300">
            <Shield className="w-3.5 h-3.5 text-[#00F0FF]" />
            <span>gVisor Sentry Kernel: Active</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-[11px] text-emerald-300">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>BigQuery Storage Write: 100% SLA</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
