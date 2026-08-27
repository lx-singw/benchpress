"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from "recharts";
import { TrajectoryTurnEvent } from "@/lib/types";

interface TokenWaterfallChartProps {
  turns: TrajectoryTurnEvent[];
}

export function TokenWaterfallChart({ turns }: TokenWaterfallChartProps) {
  const chartData = turns.map((t) => ({
    turn: `Turn ${t.turn_index}`,
    input: t.prompt_tokens,
    output: t.completion_tokens,
    reasoning: t.reasoning_tokens || 0,
    cost: t.turn_cost_usd,
    model: t.model_id,
  }));

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center border border-white/5 rounded-xl bg-black/40 text-xs font-mono text-zinc-500">
        Awaiting live trajectory turns...
      </div>
    );
  }

  return (
    <div className="h-72 w-full p-4 rounded-xl border border-white/10 bg-obsidian-900/60 backdrop-blur-xl">
      <div className="flex items-center justify-between text-xs font-mono mb-3">
        <span className="text-zinc-300 font-semibold">Turn-by-Turn Token Burn Waterfall</span>
        <span className="text-[#00F0FF]">Live FinOps Stream</span>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="turn" stroke="#94A3B8" fontSize={11} fontStyle="monospace" />
          <YAxis stroke="#94A3B8" fontSize={11} fontStyle="monospace" />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(10, 13, 20, 0.95)",
              borderColor: "rgba(255,255,255,0.15)",
              borderRadius: "8px",
              fontFamily: "monospace",
              fontSize: "11px",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
          <Bar dataKey="input" name="Input Tokens" stackId="a" fill="#00F0FF" />
          <Bar dataKey="output" name="Output Tokens" stackId="a" fill="#10B981" />
          <Bar dataKey="reasoning" name="Reasoning Tokens" stackId="a" fill="#8B5CF6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
