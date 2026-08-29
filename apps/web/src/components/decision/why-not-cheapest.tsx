import React from "react";
import { AlertOctagon, HelpCircle, ShieldX, TrendingDown, CheckCircle2 } from "lucide-react";

interface WhyNotCheapestProps {
  whyNotCheapest?: string;
  whatWouldReverseIt?: string;
}

export function WhyNotCheapest({ whyNotCheapest, whatWouldReverseIt }: WhyNotCheapestProps) {
  const explanation =
    whyNotCheapest ||
    "gemini-2.5-flash was $0.075/1M tokens (16x cheaper per raw token), but failed 2 out of 4 deterministic task assertions (TASK-003 Unicode Chunking & TASK-004 AST Regex Boundary). Under failure-inclusive CPR accounting, unguided cheap models produce infinite resolution cost on failing tasks.";

  const reversal =
    whatWouldReverseIt ||
    "Candidate configuration experiencing quality regression on canary suite or provider pricing increase > 35%.";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Primary Why Not Cheapest Callout */}
      <div className="lg:col-span-2 rounded-2xl bg-gradient-to-br from-[#1A1215]/80 via-[#120F15]/90 to-[#0A0D14] backdrop-blur-xl border border-rose-500/30 p-6 lg:p-7 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-rose-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Why Not the Cheapest Model?
            </h3>
            <p className="text-xs text-rose-300/80 font-mono">
              Empirical Elimination of Dominated Configurations
            </p>
          </div>
        </div>

        <p className="text-sm text-gray-200 leading-relaxed font-sans mb-4">
          {explanation}
        </p>

        {/* Breakdown of Why the Cheaper Model Failed */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-white/10 text-xs font-mono">
          <div className="rounded-lg bg-black/40 border border-rose-500/20 p-3">
            <div className="text-rose-400 font-semibold flex items-center gap-1.5 mb-1">
              <ShieldX className="w-4 h-4" />
              gemini-2.5-flash ($0.075 / 1M)
            </div>
            <div className="text-gray-400 text-[11px] space-y-1">
              <div>• Resolution Rate: <span className="text-rose-400 font-bold">50.0% (2/4)</span></div>
              <div>• Failure Reasons: <span className="text-rose-300">ORACLE_ASSERTION_FAILED</span></div>
              <div>• Effective CPR: <span className="text-rose-400 font-bold">Infinite / Degraded</span></div>
            </div>
          </div>

          <div className="rounded-lg bg-emerald-500/[0.06] border border-emerald-500/30 p-3">
            <div className="text-emerald-400 font-semibold flex items-center gap-1.5 mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Selected Candidate (t=2048)
            </div>
            <div className="text-gray-300 text-[11px] space-y-1">
              <div>• Resolution Rate: <span className="text-emerald-400 font-bold">100.0% (4/4)</span></div>
              <div>• Failure Reasons: <span className="text-emerald-400 font-bold">None (0 failures)</span></div>
              <div>• Effective CPR: <span className="text-emerald-400 font-bold">$0.005400 / pass</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* What Would Reverse It Box */}
      <div className="rounded-2xl bg-[#0D121F]/80 backdrop-blur-xl border border-white/10 p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2.5 mb-3 text-cyan-400">
            <TrendingDown className="w-5 h-5" />
            <h4 className="text-sm font-bold text-white tracking-tight">
              What Would Reverse This Decision?
            </h4>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed font-sans">
            {reversal}
          </p>
        </div>

        <div className="mt-4 pt-3 border-t border-white/10 text-[11px] font-mono text-gray-500">
          Continuous canary sentinels run on each deployment. If quality degrades below 75%, atomic CAS initiates instant fallback.
        </div>
      </div>
    </div>
  );
}
