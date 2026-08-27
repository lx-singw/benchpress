"use client";

import React from "react";
import { Sliders, DollarSign, Target, Gauge } from "lucide-react";
import { ParetoFilterWeights } from "@/lib/pareto-math";

interface ParetoWeightSlidersProps {
  weights: ParetoFilterWeights;
  onChange: (weights: ParetoFilterWeights) => void;
}

export function ParetoWeightSliders({ weights, onChange }: ParetoWeightSlidersProps) {
  const handleCostSlider = (val: number) => {
    const costWeight = val / 100;
    const accuracyWeight = (100 - val) / 100;
    onChange({
      ...weights,
      costWeight,
      accuracyWeight,
    });
  };

  const handleLatencySlider = (val: number) => {
    onChange({
      ...weights,
      maxLatencySlaSec: val,
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.02]">
      {/* Cost vs Accuracy Balance Slider */}
      <div>
        <div className="flex justify-between items-center text-xs font-mono mb-2">
          <span className="text-zinc-300 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-[#00F0FF]" />
            Objective Weight: Cost vs. Accuracy
          </span>
          <span className="text-[#00F0FF] font-bold">
            {Math.round(weights.accuracyWeight * 100)}% Acc / {Math.round(weights.costWeight * 100)}% Cost
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={Math.round(weights.costWeight * 100)}
          onChange={(e) => handleCostSlider(Number(e.target.value))}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-[#00F0FF]"
        />
        <div className="flex justify-between text-[10px] text-zinc-500 font-mono mt-1">
          <span>Max Accuracy (100%)</span>
          <span>Balanced (50/50)</span>
          <span>Max FinOps Cost (100%)</span>
        </div>
      </div>

      {/* Latency SLA Slider */}
      <div>
        <div className="flex justify-between items-center text-xs font-mono mb-2">
          <span className="text-zinc-300 flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-amber-400" />
            Max Turn Latency SLA Ceiling
          </span>
          <span className="text-amber-400 font-bold">{weights.maxLatencySlaSec}s SLA</span>
        </div>
        <input
          type="range"
          min={10}
          max={40}
          step={2}
          value={weights.maxLatencySlaSec}
          onChange={(e) => handleLatencySlider(Number(e.target.value))}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
        />
        <div className="flex justify-between text-[10px] text-zinc-500 font-mono mt-1">
          <span>10s (Fastest)</span>
          <span>25s (Standard)</span>
          <span>40s (High Reasoning)</span>
        </div>
      </div>
    </div>
  );
}
