import React from "react";
import { AlertOctagon, TrendingDown } from "lucide-react";

interface WhyNotCheapestProps {
  whyNotCheapest?: string;
  whatWouldReverseIt?: string;
}

export function WhyNotCheapest({ whyNotCheapest, whatWouldReverseIt }: WhyNotCheapestProps) {
  const explanation = whyNotCheapest ?? "No retained cheapest-candidate comparison is available.";
  const reversal = whatWouldReverseIt ?? "No versioned reversal criterion is available.";

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
          Reversal criteria must come from the stored, versioned decision receipt.
        </div>
      </div>
    </div>
  );
}
