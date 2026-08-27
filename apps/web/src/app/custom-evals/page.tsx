"use client";

import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, GitBranch, Cpu, Terminal, Key, Database, RefreshCw, CheckCircle2 } from "lucide-react";

export default function CustomEvalsPage() {
  const [repoUrl, setRepoUrl] = useState("git@github.com:enterprise-org/settlement-core.git");
  const [baseCommit, setBaseCommit] = useState("a8f3b2c1");
  const [testCmd, setTestCmd] = useState("pytest tests/ -k 'test_settlement_reconciliation'");
  const [canaryEnabled, setCanaryEnabled] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitSuccess(true);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#07090E] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-3.5 h-3.5" />
                VPC-SC Perimeter Active
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Key className="w-3.5 h-3.5" />
                CMEK Encrypted
              </span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white mt-2">
              Enterprise Benchmark Ingestion Portal
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Ingest proprietary git repositories and evaluate autonomous models in isolated gVisor sandboxes with anti-contamination canaries.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-xl shadow-2xl">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-indigo-400" />
                Repository Task Manifest
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                    Private Git Repository URL (SSH / HTTPS)
                  </label>
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono"
                    placeholder="git@github.com:enterprise/repo.git"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                      Base Commit / Tag
                    </label>
                    <input
                      type="text"
                      value={baseCommit}
                      onChange={(e) => setBaseCommit(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                      Max Budget Cap ($)
                    </label>
                    <input
                      type="number"
                      defaultValue={1.0}
                      step={0.1}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
                    Ground-Truth Assertion Command
                  </label>
                  <div className="relative">
                    <Terminal className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="text"
                      value={testCmd}
                      onChange={(e) => setTestCmd(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                      required
                    />
                  </div>
                </div>

                {/* Canary Toggle */}
                <div className="p-4 bg-slate-950/80 border border-slate-800/80 rounded-lg flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium text-white flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-amber-400" />
                      Dynamic Anti-Contamination Canary Ingestion
                    </div>
                    <div className="text-xs text-slate-400">
                      Injects <code className="text-indigo-300">BENCHPRESS-CANARY-GUID</code> and mutates AST holdout fixtures.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={canaryEnabled}
                    onChange={(e) => setCanaryEnabled(e.target.checked)}
                    className="w-4 h-4 accent-indigo-500 rounded cursor-pointer"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium py-2.5 px-4 rounded-lg transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Synthesizing Sandbox Task...
                    </>
                  ) : (
                    <>
                      <Cpu className="w-4 h-4" />
                      Synthesize & Ingest Enterprise Evaluation Task
                    </>
                  )}
                </button>
              </form>

              {submitSuccess && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>
                    Task ingested successfully with Canary GUID <code className="text-white font-mono">4b29f8a1-7c93-4e02-91f6-bf3a2016de90</code> into CMEK encrypted queue.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Security Perimeter Status */}
          <div className="space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-xl">
              <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400" />
                Enterprise Security State
              </h2>

              <ul className="space-y-3 text-xs">
                <li className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400">VPC-SC Perimeter</span>
                  <span className="text-emerald-400 font-medium font-mono">ENFORCED</span>
                </li>
                <li className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400">Cloud KMS CMEK</span>
                  <span className="text-cyan-400 font-medium font-mono">90-DAY ROTATION</span>
                </li>
                <li className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400">Prompt Armor</span>
                  <span className="text-indigo-400 font-medium font-mono">XML DELIMITED</span>
                </li>
                <li className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400">Emergency Kill-Switch</span>
                  <span className="text-emerald-400 font-medium font-mono">&lt;100ms READY</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
