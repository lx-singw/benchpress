"use client";

import React, { useState } from "react";
import { DollarSign, TrendingDown, Zap, ArrowRight } from "lucide-react";

export function SavingsCalculatorCard() {
  const [monthlyTasks, setMonthlyTasks] = useState<number>(5000);

  const frontierCost = monthlyTasks * 1.48; // Claude 3.7 Sonnet ($1.48 / task)
  const benchpressCost = monthlyTasks * 0.185; // Benchpress 2-Tier ($0.185 / task)
  const netSavings = frontierCost - benchpressCost;
  const savingsPct = Math.round((netSavings / frontierCost) * 100);

  return (
    <div className="p-5 rounded-xl border border-white/10 bg-obsidian-900/70 backdrop-blur-xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
            Monthly Cost Arbitrage Estimator
          </span>
        </div>
        <span className="text-xs font-mono bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-bold">
          {savingsPct}% Savings
        </span>
      </div>

      <div>
        <div className="flex justify-between text-xs font-mono text-zinc-400 mb-1.5">
          <span>Monthly Automated Coding Tasks:</span>
          <span className="text-white font-bold">{monthlyTasks.toLocaleString()} tasks</span>
        </div>
        <input
          type="range"
          min={500}
          max={50000}
          step={500}
          value={monthlyTasks}
          onChange={(e) => setMonthlyTasks(Number(e.target.value))}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/5 text-xs font-mono">
        <div className="p-2.5 rounded bg-black/40 border border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Monolithic Frontier Spend</div>
          <div className="text-sm font-bold text-rose-400 mt-0.5">${Math.round(frontierCost).toLocaleString()} / mo</div>
        </div>

        <div className="p-2.5 rounded bg-emerald-950/30 border border-emerald-500/20">
          <div className="text-[10px] text-emerald-400 uppercase">Benchpress 2-Tier Spend</div>
          <div className="text-sm font-bold text-emerald-300 mt-0.5">${Math.round(benchpressCost).toLocaleString()} / mo</div>
        </div>
      </div>
    </div>
  );
}
