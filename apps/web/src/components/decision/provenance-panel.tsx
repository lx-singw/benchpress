"use client";

import React, { useState } from "react";
import { Download, ShieldCheck, Copy, Check, Terminal, ExternalLink } from "lucide-react";
import type { DecisionReceipt } from "@benchpress/contracts";

interface ProvenancePanelProps {
  receipt: DecisionReceipt;
}

export function ProvenancePanel({ receipt }: ProvenancePanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyHash = () => {
    navigator.clipboard.writeText(receipt.evidence_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(receipt, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `benchpress_receipt_${receipt.receipt_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="rounded-2xl bg-[#0D121F]/80 backdrop-blur-xl border border-white/10 p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Cryptographic Provenance & Receipt Verification
            </h3>
            <p className="text-xs text-gray-400 font-mono">
              RFC 8785 Canonical JSON Digest & Immutable Audit Chain
            </p>
          </div>
        </div>

        <button
          onClick={handleDownload}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs transition-all shadow-[0_0_20px_rgba(6,182,212,0.25)] cursor-pointer"
        >
          <Download className="w-4 h-4" />
          Download Verified Receipt (JSON)
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        <div className="space-y-3 bg-black/40 p-4 rounded-xl border border-white/5">
          <div>
            <div className="text-gray-500 text-[10px] uppercase">Receipt ID</div>
            <div className="text-cyan-300 font-bold text-sm mt-0.5">{receipt.receipt_id}</div>
          </div>

          <div>
            <div className="text-gray-500 text-[10px] uppercase">Decision ID</div>
            <div className="text-gray-300 mt-0.5">{receipt.decision_id}</div>
          </div>

          <div>
            <div className="text-gray-500 text-[10px] uppercase">Experiment ID</div>
            <div className="text-gray-300 mt-0.5">{receipt.experiment_id}</div>
          </div>
        </div>

        <div className="space-y-3 bg-black/40 p-4 rounded-xl border border-white/5">
          <div>
            <div className="text-gray-500 text-[10px] uppercase">Git Code Commit SHA</div>
            <div className="text-emerald-400 mt-0.5 font-bold">{receipt.code_commit_sha}</div>
          </div>

          <div>
            <div className="flex items-center justify-between text-gray-500 text-[10px] uppercase">
              <span>Evidence SHA-256 Hash</span>
              <button
                onClick={handleCopyHash}
                className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <div className="text-gray-300 text-[10px] break-all mt-0.5">{receipt.evidence_hash}</div>
          </div>

          <div className="flex items-center justify-between text-gray-400 text-[11px] pt-1">
            <span>Direct API Endpoint:</span>
            <a
              href={`/api/v1/receipts/${receipt.receipt_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-cyan-400 hover:underline flex items-center gap-1"
            >
              /api/v1/receipts/{receipt.receipt_id}
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
