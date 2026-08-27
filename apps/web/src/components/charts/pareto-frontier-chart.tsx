"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  CartesianGrid,
} from "recharts";
import { Sparkles, Compass, ShieldCheck } from "lucide-react";
import { BENCHMARK_MODELS } from "@/lib/mock-data";
import { ParetoMath, ParetoFilterWeights } from "@/lib/pareto-math";
import { ParetoWeightSliders } from "./pareto-weight-sliders";

interface ParetoFrontierChartProps {
  onSelectModel?: (modelId: string) => void;
}

export function ParetoFrontierChart({ onSelectModel }: ParetoFrontierChartProps) {
  const [weights, setWeights] = useState<ParetoFilterWeights>({
    accuracyWeight: 0.5,
    costWeight: 0.5,
    maxLatencySlaSec: 35,
  });

  // Listen to spoken voice copilot weight change events
  useEffect(() => {
    const handleVoiceSync = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail?.action === "UPDATE_PARETO_WEIGHTS" && customEvent.detail.costWeight !== undefined) {
        const cw = customEvent.detail.costWeight;
        setWeights((prev) => ({
          ...prev,
          costWeight: cw,
          accuracyWeight: 1.0 - cw,
        }));
      }
    };

    window.addEventListener("benchpress:dom-sync", handleVoiceSync);
    return () => window.removeEventListener("benchpress:dom-sync", handleVoiceSync);
  }, []);

  const paretoPoints = useMemo(() => {
    return ParetoMath.computeParetoFrontier(BENCHMARK_MODELS, weights);
  }, [weights]);

  // Curve data connecting the Pareto set in order of increasing CPR
  const frontierCurveData = useMemo(() => {
    return paretoPoints
      .filter((p) => p.is_pareto_frontier)
      .map((p) => ({
        cpr_usd: p.cpr_usd,
        pass_at_1: p.pass_at_1 * 100,
        name: p.name,
      }));
  }, [paretoPoints]);

  const recommendedPoint = useMemo(() => {
    return paretoPoints.find((p) => p.is_recommended) || paretoPoints[0];
  }, [paretoPoints]);

  // Node color helper
  const getNodeFill = (p: any) => {
    if (p.provider === "Benchpress Hybrid") return "#10B981"; // Emerald
    if (p.provider === "Google") return "#00F0FF"; // Cyan
    if (p.provider === "Anthropic") return "#F59E0B"; // Amber
    if (p.provider === "OpenAI") return "#8B5CF6"; // Violet
    return "#94A3B8";
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="rounded-xl border border-white/15 bg-obsidian-900/95 p-3.5 shadow-2xl backdrop-blur-xl font-mono text-xs space-y-1 z-50">
          <div className="font-bold text-white flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: getNodeFill(data) }}
            />
            {data.name}
          </div>
          <div className="text-zinc-400">Provider: {data.provider}</div>
          <div className="flex justify-between gap-4 text-emerald-400">
            <span>Cost per Resolution (CPR):</span>
            <span className="font-bold">${data.cpr_usd.toFixed(3)}</span>
          </div>
          <div className="flex justify-between gap-4 text-[#00F0FF]">
            <span>Pass@1 Accuracy:</span>
            <span className="font-bold">{(data.pass_at_1 * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between gap-4 text-zinc-400">
            <span>Mean Latency:</span>
            <span>{data.latency_sec}s</span>
          </div>
          {data.is_pareto_frontier && (
            <div className="mt-1 pt-1 border-t border-white/10 text-amber-300 font-semibold flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Gold Pareto Efficient Set
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-xl border border-white/10 bg-obsidian-900/80 p-6 shadow-2xl backdrop-blur-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-mono tracking-widest text-emerald-400 uppercase font-semibold">
              Modality 3: Interactive Tactile Canvas
            </span>
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-2">
            2D Pareto Frontier & Dynamic Model Router <Compass className="w-5 h-5 text-[#00F0FF]" />
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time frontier optimization balancing SWE-bench Verified Pass@1 vs. Cost Per Resolution (CPR).
          </p>
        </div>

        {recommendedPoint && (
          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs font-mono">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-[10px] text-zinc-400 uppercase">Optimal Operating Point:</div>
              <div className="text-emerald-300 font-bold">{recommendedPoint.name}</div>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Weight Sliders */}
      <ParetoWeightSliders weights={weights} onChange={setWeights} />

      {/* Recharts Scatter & Line Canvas */}
      <div className="h-[360px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            margin={{ top: 20, right: 30, bottom: 20, left: 10 }}
            onClick={(e: any) => {
              if (e && e.activePayload && e.activePayload[0]) {
                const point = e.activePayload[0].payload;
                if (point.model_id && onSelectModel) {
                  onSelectModel(point.model_id);
                }
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              type="number"
              dataKey="cpr_usd"
              name="Cost Per Resolution (USD)"
              unit="$"
              domain={[0.02, 2.0]}
              tick={{ fill: "#94A3B8", fontSize: 11, fontFamily: "monospace" }}
              label={{
                value: "Cost Per Resolution ($ / task) → (Lower is Better)",
                position: "insideBottom",
                offset: -12,
                fill: "#94A3B8",
                fontSize: 11,
                fontFamily: "monospace",
              }}
            />
            <YAxis
              type="number"
              dataKey="pass_at_1"
              name="Pass@1 Accuracy (%)"
              unit="%"
              domain={[45, 80]}
              tick={{ fill: "#94A3B8", fontSize: 11, fontFamily: "monospace" }}
              label={{
                value: "SWE-bench Pass@1 (%) → (Higher is Better)",
                angle: -90,
                position: "insideLeft",
                offset: 5,
                fill: "#94A3B8",
                fontSize: 11,
                fontFamily: "monospace",
              }}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Pareto Non-Dominated Frontier Curve */}
            <Line
              type="monotone"
              data={frontierCurveData.map((d) => ({ ...d, pass_at_1: d.pass_at_1 }))}
              dataKey="pass_at_1"
              stroke="#F59E0B"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={true}
            />

            {/* All Model Nodes */}
            <Scatter
              name="Models"
              data={paretoPoints.map((p) => ({ ...p, pass_at_1: p.pass_at_1 * 100 }))}
              fill="#00F0FF"
            >
              {paretoPoints.map((entry, index) => (
                <circle
                  key={`node-${index}`}
                  cx={0}
                  cy={0}
                  r={entry.is_recommended ? 9 : entry.is_pareto_frontier ? 7 : 5}
                  fill={getNodeFill(entry)}
                  stroke={entry.is_recommended ? "#FFFFFF" : entry.is_pareto_frontier ? "#F59E0B" : "transparent"}
                  strokeWidth={entry.is_recommended ? 2.5 : 1.5}
                  className="cursor-pointer hover:opacity-80 transition-all"
                />
              ))}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Legend & Provider Color Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono border-t border-white/5 pt-3 text-zinc-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" /> Benchpress 2-Tier
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00F0FF]" /> Google Gemini
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" /> Anthropic Claude
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6]" /> OpenAI
          </span>
        </div>

        <div className="flex items-center gap-2 text-amber-400">
          <span className="w-4 h-0.5 border-t border-dashed border-amber-400" />
          <span>Gold Pareto Non-Dominated Curve</span>
        </div>
      </div>
    </div>
  );
}
