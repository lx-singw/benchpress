import React from "react";
import { ArbitrageWizard } from "@/components/arbitrage/arbitrage-wizard";
import { DollarSign, ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Economic Arbitrage & Model Migration Wizard | Benchpress",
  description: "Calculate real-time enterprise AI cost savings and generate 1-click model routing configurations.",
};

export default function ArbitragePage() {
  return (
    <div className="min-h-screen bg-[#07090E] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <DollarSign className="w-3.5 h-3.5" />
                Real-Time FinOps Arbitrage
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <ShieldCheck className="w-3.5 h-3.5" />
                Zero-Accuracy-Loss Guaranteed
              </span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white mt-2">
              Economic Arbitrage & Migration Engine
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Arbitrage foundation model pricing by dynamically orchestrating Gemini 2.5 Pro planning with sub-8s Gemini 2.5 Flash execution.
            </p>
          </div>
        </div>

        {/* Wizard Body */}
        <ArbitrageWizard />
      </div>
    </div>
  );
}
