import React from "react";
import { CheckCircle, XCircle, Clock, DollarSign, BarChart2, ShieldAlert } from "lucide-react";
import type { Aggregate } from "@benchpress/contracts";

interface EvidenceSummaryProps {
  baselineAgg?: Aggregate | null;
  candidateAgg?: Aggregate | null;
}

export function EvidenceSummary({ baselineAgg, candidateAgg }: EvidenceSummaryProps) {
  if (!baselineAgg || !candidateAgg) {
    return (
      <div className="rounded-2xl bg-[#0D121F]/80 border border-amber-500/30 p-6 text-sm text-amber-200">
        Measured aggregate evidence is unavailable for this decision. No fallback metrics are displayed.
      </div>
    );
  }

  const baseAttempts = baselineAgg.total_attempts;
  const baseResolved = baselineAgg.resolved_count;
  const baseFailed = baselineAgg.failed_count;
  const basePassRate = (baselineAgg.pass_rate * 100).toFixed(1);
  const baseCpr = baselineAgg.cpr_defined && baselineAgg.cpr_usd !== null
    ? `$${Number(baselineAgg.cpr_usd).toFixed(6)}`
    : `Undefined (${baselineAgg.cpr_undefined_reason || "NO_REASON_RECORDED"})`;
  const baseTotalCost = `$${Number(baselineAgg.total_cost_usd).toFixed(6)}`;
  const baseMeanLat = `${baselineAgg.mean_latency_ms} ms`;
  const baseP95Lat = `${baselineAgg.p95_latency_ms} ms`;
  const baseLower = (baselineAgg.pass_rate_lower_bound * 100).toFixed(1);
  const baseUpper = (baselineAgg.pass_rate_upper_bound * 100).toFixed(1);

  const candAttempts = candidateAgg.total_attempts;
  const candResolved = candidateAgg.resolved_count;
  const candFailed = candidateAgg.failed_count;
  const candPassRate = (candidateAgg.pass_rate * 100).toFixed(1);
  const candCpr = candidateAgg.cpr_defined && candidateAgg.cpr_usd !== null
    ? `$${Number(candidateAgg.cpr_usd).toFixed(6)}`
    : `Undefined (${candidateAgg.cpr_undefined_reason || "NO_REASON_RECORDED"})`;
  const candTotalCost = `$${Number(candidateAgg.total_cost_usd).toFixed(6)}`;
  const candMeanLat = `${candidateAgg.mean_latency_ms} ms`;
  const candP95Lat = `${candidateAgg.p95_latency_ms} ms`;
  const candLower = (candidateAgg.pass_rate_lower_bound * 100).toFixed(1);
  const candUpper = (candidateAgg.pass_rate_upper_bound * 100).toFixed(1);

  const passDelta = ((candidateAgg.pass_rate - baselineAgg.pass_rate) * 100).toFixed(1);
  const costDelta = baselineAgg.cpr_usd !== null && candidateAgg.cpr_usd !== null && Number(baselineAgg.cpr_usd) > 0
    ? (((Number(candidateAgg.cpr_usd) - Number(baselineAgg.cpr_usd)) / Number(baselineAgg.cpr_usd)) * 100).toFixed(1)
    : null;
  const spendDelta = Number(baselineAgg.total_cost_usd) > 0
    ? (((Number(candidateAgg.total_cost_usd) - Number(baselineAgg.total_cost_usd)) / Number(baselineAgg.total_cost_usd)) * 100).toFixed(1)
    : null;
  const latencyDelta = baselineAgg.mean_latency_ms > 0
    ? (((candidateAgg.mean_latency_ms - baselineAgg.mean_latency_ms) / baselineAgg.mean_latency_ms) * 100).toFixed(1)
    : null;

  return (
    <div className="rounded-2xl bg-[#0D121F]/80 backdrop-blur-xl border border-white/10 p-6 lg:p-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-white/10 pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-cyan-400" />
            Failure-Inclusive Empirical Evidence Summary
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Ground-truth deterministic Pytest assertion results across judged task cohort.
          </p>
        </div>
        <div className="text-[11px] font-mono text-gray-400 bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
          Uncertainty: <span className="text-cyan-300 font-semibold">95% Wilson Score Interval</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-white/10 text-gray-400">
              <th className="pb-3 font-semibold uppercase tracking-wider">Metric</th>
              <th className="pb-3 font-semibold uppercase tracking-wider text-gray-300">
                Baseline ({baselineAgg.configuration_id})
              </th>
              <th className="pb-3 font-semibold uppercase tracking-wider text-emerald-400">
                Candidate ({candidateAgg.configuration_id})
              </th>
              <th className="pb-3 font-semibold uppercase tracking-wider text-right">Delta / ROI</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-gray-300">
            {/* Resolution Rate */}
            <tr>
              <td className="py-3.5 text-gray-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Observed Resolution Rate
              </td>
              <td className="py-3.5">
                <span className="font-bold text-white">{basePassRate}%</span>{" "}
                <span className="text-gray-500">({baseResolved}/{baseAttempts} tasks)</span>
                <div className="text-[10px] text-gray-500">95% CI: [{baseLower}% – {baseUpper}%]</div>
              </td>
              <td className="py-3.5 text-emerald-300 font-bold">
                <span className="text-emerald-400">{candPassRate}%</span>{" "}
                <span className="text-emerald-500/80">({candResolved}/{candAttempts} tasks)</span>
                <div className="text-[10px] text-emerald-500/70">95% CI: [{candLower}% – {candUpper}%]</div>
              </td>
              <td className="py-3.5 text-right font-bold text-emerald-400">{Number(passDelta) >= 0 ? "+" : ""}{passDelta} pp</td>
            </tr>

            {/* Cost Per Resolution (CPR) */}
            <tr className="bg-white/[0.02]">
              <td className="py-3.5 text-gray-400 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-cyan-400" />
                Cost Per Resolution (CPR)
              </td>
              <td className="py-3.5 font-bold text-white">{baseCpr}</td>
              <td className="py-3.5 font-bold text-emerald-400 text-sm">{candCpr}</td>
              <td className="py-3.5 text-right font-bold text-emerald-400">{costDelta === null ? "Undefined" : `${costDelta}%`}</td>
            </tr>

            {/* Total Cohort Dollar Spend */}
            <tr>
              <td className="py-3.5 text-gray-400">Total Cohort Spend</td>
              <td className="py-3.5">{baseTotalCost}</td>
              <td className="py-3.5 text-emerald-300">{candTotalCost}</td>
              <td className="py-3.5 text-right text-emerald-400">{spendDelta === null ? "Undefined" : `${spendDelta}%`}</td>
            </tr>

            {/* Mean Latency */}
            <tr>
              <td className="py-3.5 text-gray-400 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                Execution Latency (Mean / P95)
              </td>
              <td className="py-3.5">{baseMeanLat} / {baseP95Lat}</td>
              <td className="py-3.5 text-gray-200">{candMeanLat} / {candP95Lat}</td>
              <td className="py-3.5 text-right text-emerald-400">{latencyDelta === null ? "Undefined" : `${latencyDelta}%`}</td>
            </tr>

            {/* Failed Attempts */}
            <tr className="bg-rose-500/[0.03]">
              <td className="py-3.5 text-gray-400 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Failed / Excluded Attempts
              </td>
              <td className="py-3.5 text-rose-300 font-bold">
                {baseFailed} failed attempts
              </td>
              <td className="py-3.5 text-emerald-400 font-bold">{candFailed} failed attempts</td>
              <td className="py-3.5 text-right text-emerald-400 font-bold">{candFailed - baseFailed} net failures</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 text-[11px] text-gray-500 font-mono flex items-center justify-between flex-wrap gap-2">
        <span>* Failure-Inclusive Law: Total Cost includes prompt/completion spend of all passed and failed runs.</span>
        <span>Oracle: Pytest 8.3.0 Deterministic Harness</span>
      </div>
    </div>
  );
}
