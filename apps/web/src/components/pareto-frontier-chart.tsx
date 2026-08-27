"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  Sliders,
  Sparkles,
  Zap,
  DollarSign,
  Clock,
  TrendingDown,
  Info,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatPercent, formatUsd } from "@/lib/utils";
import type { ParetoDataPoint } from "@/lib/types";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  Line,
} from "recharts";

const BASE_MODELS: ParetoDataPoint[] = [
  {
    modelId: "gemini-2.5-flash",
    modelName: "Gemini 2.5 Flash",
    provider: "Google",
    cprUsd: 0.12,
    passRatePct: 41.5,
    meanLatencySeconds: 6.8,
    isOnFrontier: true,
  },
  {
    modelId: "hybrid-gemini-pro-flash",
    modelName: "Hybrid: Gemini 2.5 Pro + Flash",
    provider: "Google",
    cprUsd: 0.28,
    passRatePct: 62.4,
    meanLatencySeconds: 14.2,
    isOnFrontier: true,
  },
  {
    modelId: "gemini-2.5-pro",
    modelName: "Gemini 2.5 Pro",
    provider: "Google",
    cprUsd: 0.42,
    passRatePct: 63.8,
    meanLatencySeconds: 18.4,
    isOnFrontier: true,
  },
  {
    modelId: "o3-mini",
    modelName: "o3-mini (High)",
    provider: "OpenAI",
    cprUsd: 0.76,
    passRatePct: 58.7,
    meanLatencySeconds: 28.5,
    isOnFrontier: false,
  },
  {
    modelId: "gpt-4o",
    modelName: "GPT-4o",
    provider: "OpenAI",
    cprUsd: 0.88,
    passRatePct: 48.2,
    meanLatencySeconds: 22.0,
    isOnFrontier: false,
  },
  {
    modelId: "claude-3-7-sonnet",
    modelName: "Claude 3.7 Sonnet (Thinking)",
    provider: "Anthropic",
    cprUsd: 1.15,
    passRatePct: 70.4,
    meanLatencySeconds: 32.1,
    isOnFrontier: true,
  },
];

interface ParetoFrontierChartProps {
  onSelectModel?: (modelId: string) => void;
}

export function ParetoFrontierChart({ onSelectModel }: ParetoFrontierChartProps) {
  const [costWeight, setCostWeight] = useState<number>(50); // 0 = 100% Accuracy priority, 100 = 100% Cost priority
  const [maxLatency, setMaxLatency] = useState<number>(35);
  const [activeOptimalModel, setActiveOptimalModel] = useState<ParetoDataPoint>(BASE_MODELS[1]);

  // Listen to Spoken Voice Copilot DOM sync events
  useEffect(() => {
    const handleDomSync = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail?.action === "UPDATE_PARETO_WEIGHTS" && customEvent.detail.costWeightPct !== undefined) {
        setCostWeight(customEvent.detail.costWeightPct);
      }
    };

    window.addEventListener("benchpress:dom-sync", handleDomSync);
    return () => window.removeEventListener("benchpress:dom-sync", handleDomSync);
  }, []);

  // Recalculate optimal model based on costWeight & maxLatency
  useEffect(() => {
    const eligible = BASE_MODELS.filter((m) => m.meanLatencySeconds <= maxLatency);
    if (eligible.length === 0) {
      setActiveOptimalModel(BASE_MODELS[0]);
      return;
    }

    // Score: (accuracyWeight * normalized_pass_rate) - (costWeight * normalized_cpr)
    const accuracyWeight = 100 - costWeight;
    let bestScore = -Infinity;
    let bestModel = eligible[0];

    eligible.forEach((m) => {
      // Normalize CPR (lower is better) and PassRate (higher is better)
      const accScore = m.passRatePct / 100.0;
      const costPenalty = m.cprUsd / 1.5;
      const score = (accuracyWeight / 100) * accScore - (costWeight / 100) * costPenalty;

      if (score > bestScore) {
        bestScore = score;
        bestModel = m;
      }
    });

    setActiveOptimalModel(bestModel);
    if (onSelectModel) {
      onSelectModel(bestModel.modelId);
    }
  }, [costWeight, maxLatency, onSelectModel]);

  return (
    <GlassCard className="p-6 flex flex-col justify-between" glow="none">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#00F0FF]/10 text-[#00F0FF]">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm">Interactive Pareto Economic Frontier</h3>
              <p className="text-[11px] text-gray-400">Tactile Optimization & Frontier Modeling</p>
            </div>
          </div>

          <Badge variant="cyan" size="sm">
            Modality 3: Canvas
          </Badge>
        </div>

        {/* 2D Scatter Chart */}
        <div className="h-64 w-full my-4">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 15, right: 15, bottom: 20, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1A2234" />
              <XAxis
                type="number"
                dataKey="cprUsd"
                name="CPR"
                unit="$"
                stroke="#6B7280"
                tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }}
                domain={[0, 1.3]}
              />
              <YAxis
                type="number"
                dataKey="passRatePct"
                name="Pass Rate"
                unit="%"
                stroke="#6B7280"
                tick={{ fill: "#9CA3AF", fontSize: 11, fontFamily: "JetBrains Mono" }}
                domain={[30, 80]}
              />
              <Tooltip
                content={({ payload }) => {
                  if (!payload || payload.length === 0) return null;
                  const data = payload[0].payload as ParetoDataPoint;
                  const isSelected = data.modelId === activeOptimalModel.modelId;
                  return (
                    <div className="rounded-lg border border-white/20 bg-[#121722] p-3 text-xs shadow-2xl font-mono">
                      <div className="font-sans font-bold text-white flex items-center justify-between gap-3">
                        <span>{data.modelName}</span>
                        {isSelected && (
                          <span className="rounded bg-[#00F0FF]/20 px-1.5 py-0.5 text-[10px] text-[#00F0FF]">
                            OPTIMAL ROUTE
                          </span>
                        )}
                      </div>
                      <div className="mt-1 text-gray-400">
                        CPR: <span className="text-[#00F0FF] font-bold">{formatUsd(data.cprUsd)}</span>
                      </div>
                      <div className="text-gray-400">
                        Pass Rate: <span className="text-[#10B981] font-bold">{formatPercent(data.passRatePct)}</span>
                      </div>
                      <div className="text-gray-400">
                        Mean Latency: <span>{data.meanLatencySeconds}s</span>
                      </div>
                    </div>
                  );
                }}
              />
              <Scatter name="Models" data={BASE_MODELS} onClick={(node) => onSelectModel?.(node.modelId)}>
                {BASE_MODELS.map((entry) => {
                  const isOptimal = entry.modelId === activeOptimalModel.modelId;
                  return (
                    <Cell
                      key={`cell-${entry.modelId}`}
                      fill={isOptimal ? "#00F0FF" : entry.isOnFrontier ? "#10B981" : "#6B7280"}
                      stroke={isOptimal ? "#FFFFFF" : "transparent"}
                      strokeWidth={isOptimal ? 2 : 0}
                    />
                  );
                })}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Tactile Sliders */}
        <div className="space-y-3 rounded-xl border border-white/10 bg-[#0A0D14]/80 p-4 text-xs font-mono">
          <div>
            <div className="flex items-center justify-between text-gray-400 mb-1">
              <span className="flex items-center gap-1.5">
                <DollarSign className="h-3.5 w-3.5 text-[#00F0FF]" />
                Optimization Weight (Accuracy vs. Cost):
              </span>
              <span className="text-white font-bold">
                {costWeight}% Cost / {100 - costWeight}% Acc
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={costWeight}
              onChange={(e) => setCostWeight(parseInt(e.target.value))}
              className="w-full accent-[#00F0FF] cursor-pointer"
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-gray-400 mb-1">
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-[#F59E0B]" />
                Max Latency SLA Tolerance:
              </span>
              <span className="text-white font-bold">{maxLatency}s</span>
            </div>
            <input
              type="range"
              min="10"
              max="40"
              value={maxLatency}
              onChange={(e) => setMaxLatency(parseInt(e.target.value))}
              className="w-full accent-[#F59E0B] cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Dynamic Recommended Route Highlight */}
      <div className="mt-4 rounded-xl border border-[#00F0FF]/30 bg-gradient-to-r from-[#00F0FF]/15 to-[#10B981]/15 p-3.5 text-xs">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5 font-bold text-white">
            <Sparkles className="h-4 w-4 text-[#00F0FF]" />
            <span>Optimal Operating Route: {activeOptimalModel.modelName}</span>
          </div>
          <Badge variant="cyan" size="sm" dot>
            RECOMMENDED
          </Badge>
        </div>
        <p className="text-gray-300 text-[11px] leading-relaxed">
          At {costWeight}% cost priority with &le;{maxLatency}s latency,{" "}
          <strong className="text-white">{activeOptimalModel.modelName}</strong> maximizes Pass@1 ({formatPercent(activeOptimalModel.passRatePct)}) while maintaining ultra-low CPR of {formatUsd(activeOptimalModel.cprUsd)}.
        </p>
      </div>
    </GlassCard>
  );
}
