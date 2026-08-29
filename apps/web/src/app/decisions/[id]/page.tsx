import React from "react";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, Activity } from "lucide-react";
import { firestoreRepo } from "@/lib/server/firestore-repo";
import { SwitchDecisionCard } from "@/components/decision/switch-decision-card";
import { EvidenceSummary } from "@/components/decision/evidence-summary";
import { WhyNotCheapest } from "@/components/decision/why-not-cheapest";
import { ReplayTimeline } from "@/components/decision/replay-timeline";
import { ProvenancePanel } from "@/components/decision/provenance-panel";

interface DecisionPageProps {
  params: Promise<{ id: string }>;
}

export default async function DecisionPage({ params }: DecisionPageProps) {
  const { id } = await params;

  // Retrieve decision receipt
  const receipt = await firestoreRepo.getDecision(id);

  if (!receipt) {
    notFound();
  }

  // Retrieve associated configurations, aggregates, and replay events
  const [baseConfig, candConfig, baseAgg, candAgg, replayEvents] = await Promise.all([
    firestoreRepo.getConfiguration(receipt.baseline_configuration_id),
    receipt.candidate_configuration_id
      ? firestoreRepo.getConfiguration(receipt.candidate_configuration_id)
      : null,
    firestoreRepo.getAggregate(receipt.baseline_aggregate_id),
    receipt.candidate_aggregate_id
      ? firestoreRepo.getAggregate(receipt.candidate_aggregate_id)
      : null,
    firestoreRepo.getReplayEvents(receipt.experiment_id),
  ]);

  return (
    <div className="min-h-screen bg-[#07090E] text-gray-100 pb-20 pt-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white border border-white/10 transition-all cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">
                Autonomous Policy Governance
              </span>
              <span className="text-gray-600">•</span>
              <span className="text-xs font-mono text-gray-400">{receipt.receipt_id}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight mt-0.5">
              Taskmaster Decision Receipt & Ground-Truth Verification
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            LIVE VERIFIED RECORD
          </div>
        </div>
      </div>

      {/* 1. Hero Switch Decision Card */}
      <SwitchDecisionCard
        receipt={receipt}
        baselineConfig={baseConfig}
        candidateConfig={candConfig}
        baselineAgg={baseAgg}
        candidateAgg={candAgg}
      />

      {/* 2. Side-by-side Evidence Summary Table */}
      <EvidenceSummary baselineAgg={baseAgg} candidateAgg={candAgg} />

      {/* 3. Why Not Cheapest & Reversal Criteria */}
      <WhyNotCheapest
        whyNotCheapest={receipt.why_not_cheapest}
        whatWouldReverseIt={receipt.what_would_reverse_it}
      />

      {/* 4. Interactive 7-State Replay Timeline */}
      <ReplayTimeline events={replayEvents} />

      {/* 5. Cryptographic Provenance & 1-Click JSON Download */}
      <ProvenancePanel receipt={receipt} />
    </div>
  );
}
