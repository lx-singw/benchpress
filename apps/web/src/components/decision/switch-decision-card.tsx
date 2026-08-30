"use client";

import React from "react";
import { ArrowRight, CheckCircle, AlertTriangle, XCircle, Sparkles, Cpu, DollarSign, Layers } from "lucide-react";
import { TruthBadge } from "./truth-badge";
import type { DecisionReceipt, NativeConfiguration, Aggregate } from "@benchpress/contracts";

interface SwitchDecisionCardProps {
  receipt: DecisionReceipt;
  baselineConfig?: NativeConfiguration | null;
  candidateConfig?: NativeConfiguration | null;
  baselineAgg?: Aggregate | null;
  candidateAgg?: Aggregate | null;
}

export function SwitchDecisionCard({
  receipt,
  baselineConfig,
  candidateConfig,
  baselineAgg,
  candidateAgg,
}: SwitchDecisionCardProps) {
  const isSwitch = receipt.public_decision === "SWITCH";
  const isTestMore = receipt.public_decision === "TEST MORE";
  const isStay = receipt.public_decision === "STAY";

  let statusBorder = "border-emerald-500/40 shadow-[0_0_40px_rgba(16,185,129,0.15)]";
  let badgeBg = "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";
  let statusIcon = <CheckCircle className="w-6 h-6 text-emerald-400" />;
  let verdictTitle = "SWITCH: PROMOTE CANDIDATE CONFIGURATION";
  let verdictSub = "Verified quality gain, positive ROI & passing canary guardrails.";

  if (isTestMore) {
    statusBorder = "border-amber-500/40 shadow-[0_0_40px_rgba(245,158,11,0.15)]";
    badgeBg = "bg-amber-500/20 text-amber-400 border-amber-500/50";
    statusIcon = <AlertTriangle className="w-6 h-6 text-amber-400" />;
    verdictTitle = "TEST MORE: EVIDENCE INSUFFICIENT";
    verdictSub = "Statistically overlapping confidence intervals or active benchmark drift.";
  } else if (isStay) {
    statusBorder = "border-rose-500/40 shadow-[0_0_40px_rgba(244,63,94,0.15)]";
    badgeBg = "bg-rose-500/20 text-rose-400 border-rose-500/50";
    statusIcon = <XCircle className="w-6 h-6 text-rose-400" />;
    verdictTitle = "STAY: RETAIN BASELINE CONFIGURATION";
    verdictSub = "Candidate configuration rejected due to quality breach or dominated CPR.";
  }

  const baseCpr = baselineAgg
    ? baselineAgg.cpr_defined && baselineAgg.cpr_usd !== null
      ? `$${Number(baselineAgg.cpr_usd).toFixed(6)}`
      : `Undefined (${baselineAgg.cpr_undefined_reason || "NO_REASON_RECORDED"})`
    : "Unavailable";
  const candCpr = candidateAgg
    ? candidateAgg.cpr_defined && candidateAgg.cpr_usd !== null
      ? `$${Number(candidateAgg.cpr_usd).toFixed(6)}`
      : `Undefined (${candidateAgg.cpr_undefined_reason || "NO_REASON_RECORDED"})`
    : "Unavailable";
  const basePass = baselineAgg ? `${(baselineAgg.pass_rate * 100).toFixed(1)}% (${baselineAgg.resolved_count}/${baselineAgg.total_attempts})` : "Unavailable";
  const candPass = candidateAgg ? `${(candidateAgg.pass_rate * 100).toFixed(1)}% (${candidateAgg.resolved_count}/${candidateAgg.total_attempts})` : "Unavailable";

  const cprSavings =
    baselineAgg && candidateAgg && baselineAgg.cpr_usd !== null && candidateAgg.cpr_usd !== null && Number(baselineAgg.cpr_usd) > 0
      ? (((Number(baselineAgg.cpr_usd) - Number(candidateAgg.cpr_usd)) / Number(baselineAgg.cpr_usd)) * 100).toFixed(1)
      : null;

  return (
    <div className={`relative overflow-hidden rounded-2xl bg-[#0D121F]/90 backdrop-blur-xl border ${statusBorder} p-6 lg:p-8 transition-all`}>
      {/* Ambient background glow */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      {isSwitch && (
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      )}

      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 shadow-inner">
            {statusIcon}
          </div>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider border uppercase ${badgeBg}`}>
                {receipt.public_decision}
              </span>
              <TruthBadge truthClass={receipt.truth_class} size="sm" />
            </div>
            <h2 className="text-xl lg:text-2xl font-bold text-white mt-2 tracking-tight">
              {verdictTitle}
            </h2>
            <p className="text-sm text-gray-400 mt-0.5">{verdictSub}</p>
          </div>
        </div>

        <div className="flex flex-col items-end text-xs font-mono text-gray-400 bg-black/40 px-4 py-2.5 rounded-lg border border-white/5">
          <span className="text-gray-500">CORRELATION ID</span>
          <span className="text-cyan-300 font-semibold">{receipt.correlation_id}</span>
          <span className="text-gray-500 mt-1">SEGMENT</span>
          <span className="text-gray-300">{receipt.task_segment_id}</span>
        </div>
      </div>

      {/* Headline Rationale */}
      <div className="my-6 p-4 rounded-xl bg-white/[0.03] border border-white/10">
        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 font-semibold uppercase tracking-wider mb-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Decision Rationale
        </div>
        <p className="text-sm lg:text-base text-gray-200 leading-relaxed">
          {receipt.why_decision}
        </p>
      </div>

      {/* Side-by-Side Configuration Diff Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {/* Baseline Card */}
        <div className="rounded-xl bg-black/40 border border-white/10 p-5">
          <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-3">
            <span className="text-xs font-mono text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-gray-500" />
              Active Baseline Policy
            </span>
            <span className="text-[11px] font-mono text-gray-500">{receipt.baseline_configuration_id}</span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-gray-400">Request Model:</span>
              <span className="text-gray-200 font-semibold">{baselineConfig?.request_model ?? "Unavailable"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Thinking Budget:</span>
              <span className="text-gray-400">{baselineConfig ? `${baselineConfig.thinking_budget_tokens} tokens` : "Unavailable"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Resolution Rate:</span>
              <span className="text-gray-200 font-semibold">{basePass}</span>
            </div>
            <div className="flex justify-between border-t border-white/5 pt-2">
              <span className="text-gray-400">Cost Per Resolution:</span>
              <span className="text-gray-200 font-bold text-sm">{baseCpr}</span>
            </div>
          </div>
        </div>

        {/* Candidate Card */}
        <div className="rounded-xl bg-emerald-500/[0.04] border border-emerald-500/30 p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-xl pointer-events-none" />

          <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
            <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              Candidate Configuration
            </span>
            <span className="text-[11px] font-mono text-emerald-400/80">{receipt.candidate_configuration_id}</span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-gray-400">Request Model:</span>
              <span className="text-emerald-300 font-semibold">{candidateConfig?.request_model ?? "Unavailable"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Thinking Budget:</span>
              <span className="text-cyan-400 font-bold">{candidateConfig ? `${candidateConfig.thinking_budget_tokens} tokens` : "Unavailable"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Resolution Rate:</span>
              <span className="text-emerald-400 font-bold">{candPass}</span>
            </div>
            <div className="flex justify-between border-t border-emerald-500/20 pt-2">
              <span className="text-emerald-400 font-semibold">Cost Per Resolution:</span>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400 font-bold text-sm">{candCpr}</span>
                {cprSavings !== null && (
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                    -{cprSavings}% CPR
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
