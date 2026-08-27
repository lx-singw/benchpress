"use client";

import React, { useState } from "react";
import { Sparkles, DollarSign, TrendingDown, ArrowRight, ShieldCheck, X } from "lucide-react";

export function WhySwitchWidget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-xs font-mono text-emerald-300 transition shadow-sm"
      >
        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
        <span>Why Switch? (87.5% ROI)</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 bottom-full mb-2 w-80 rounded-xl border border-white/15 bg-obsidian-900/95 p-4 shadow-2xl backdrop-blur-2xl text-xs font-mono z-50 animate-in fade-in slide-in-from-bottom-2 space-y-3">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <div className="flex items-center gap-1.5 font-bold text-white">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <span>Model Routing Arbitrage</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-zinc-500 hover:text-white transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-zinc-300 font-sans text-xs leading-relaxed">
            Frontier models (Claude 3.7 Sonnet / GPT-4.5) charge up to $1.48 per resolved task on SWE-bench.
          </p>

          <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 space-y-1">
            <div className="text-[10px] text-emerald-400 uppercase font-semibold">
              Benchpress 2-Tier Strategy
            </div>
            <div className="text-sm font-bold text-white flex items-center justify-between">
              <span>$0.185 CPR</span>
              <span className="text-emerald-400 text-xs font-normal">-87.5% Cost</span>
            </div>
            <p className="text-[11px] text-zinc-400 font-sans">
              Gemini 2.5 Pro (Planner) + Gemini 2.5 Flash (Coder) with zero accuracy regression (71.2% Pass@1).
            </p>
          </div>

          <div className="pt-1 text-[10px] text-zinc-500 flex items-center justify-between">
            <span>Drop-in OpenAI proxy</span>
            <span className="text-[#00F0FF]">/api/v1/proxy/</span>
          </div>
        </div>
      )}
    </div>
  );
}
