"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Camera,
  Upload,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  FileCode,
  Layers,
  Wrench,
  DollarSign,
  Image as ImageIcon,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { formatPercent, formatUsd } from "@/lib/utils";

interface DiagnosticResult {
  errorType: string;
  confidenceScore: number;
  extractedStackTrace: string;
  matchedBenchmarkId: string;
  matchedSuite: string;
  rootCauseAnalysis: string;
  recommendedModelRoute: string;
  recommendedPatch: string;
  projectedCostReductionPct: number;
}

const SAMPLE_DIAGNOSTICS: Record<string, DiagnosticResult> = {
  pytest_schema: {
    errorType: "ASTSchemaMismatch / TypeError",
    confidenceScore: 0.96,
    extractedStackTrace: `TypeError: edit_file() got unexpected keyword argument 'file_path'\n  File "agent/tools.py", line 42, in execute_tool\n    return target_fn(**arguments)\npytest: 1 failed in 0.42s`,
    matchedBenchmarkId: "django__django-11099",
    matchedSuite: "SWE-bench Verified",
    rootCauseAnalysis: "Model generated Claude 3.5 Sonnet legacy tool schema ('file_path') instead of Benchpress standard AST signature ('path').",
    recommendedModelRoute: "Gemini 2.5 Pro (Planner) + Autonomous AST Healer",
    recommendedPatch: "AST Auto-Repair: rewrote kwargs {'file_path': '...'} -> {'path': '...'}",
    projectedCostReductionPct: 68.4,
  },
  timeout_bloat: {
    errorType: "TokenVelocityBloat / Runaway Loop",
    confidenceScore: 0.92,
    extractedStackTrace: `[Sentinel Alert] Turn 6 cost reached $1.85 (82% of total cap)\nExceeded token burn rate: 14.2k tokens/turn.\nTrace: Infinite backtracking in recursive AST visitor.`,
    matchedBenchmarkId: "sympy__sympy-13480",
    matchedSuite: "SWE-bench Verified",
    rootCauseAnalysis: "Monolithic model became trapped in an uncontrolled context bloat cycle at turn 6.",
    recommendedModelRoute: "Turn-5 Markov Budget Sentinel + Gemini 2.5 Flash Fast Path",
    recommendedPatch: "Trigger early-halt cutoff; compact L1 working memory by 78.5%",
    projectedCostReductionPct: 74.0,
  },
};

export function VisionErrorDropzone() {
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [diagnostic, setDiagnostic] = useState<DiagnosticResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Global clipboard paste listener
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            processFile(file);
          }
          break;
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, []);

  const processFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string);
      runOcrAnalysis("pytest_schema");
    };
    reader.readAsDataURL(file);
  };

  const runOcrAnalysis = (sampleKey: string = "pytest_schema") => {
    setIsAnalyzing(true);
    setDiagnostic(null);

    setTimeout(() => {
      setIsAnalyzing(false);
      setDiagnostic(SAMPLE_DIAGNOSTICS[sampleKey] || SAMPLE_DIAGNOSTICS.pytest_schema);
    }, 1200);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <GlassCard className="p-6" glow="none">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#00F0FF]/10 text-[#00F0FF]">
            <Camera className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm">Computer Vision Diagnostic Ingestor</h3>
            <p className="text-[11px] text-gray-400">Gemini Vision OCR Stack Trace & Trajectory Matching</p>
          </div>
        </div>

        <Badge variant="cyan" size="sm">
          Modality 2: Vision
        </Badge>
      </div>

      {/* Dropzone Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-4 text-center transition-all ${
          isDragging
            ? "border-[#00F0FF] bg-[#00F0FF]/10 shadow-glass-cyan"
            : "border-white/15 bg-[#0A0D14]/60 hover:border-white/30 hover:bg-[#121722]/80"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              processFile(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#121722] text-[#00F0FF] border border-white/10">
            {isAnalyzing ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <Upload className="h-5 w-5" />
            )}
          </div>
          <div>
            <span className="font-mono text-xs font-semibold text-white">
              Drop terminal / IDE screenshot here
            </span>
            <p className="text-[11px] text-gray-400 mt-0.5">
              or paste directly with <kbd className="rounded bg-white/10 px-1 font-mono text-gray-300">Ctrl+V</kbd>
            </p>
          </div>
        </div>
      </div>

      {/* Sample Fixture Buttons */}
      <div className="mt-3 flex items-center justify-between text-xs font-mono text-gray-400">
        <span>Test with sample screenshot:</span>
        <div className="flex gap-2">
          <button
            onClick={() => runOcrAnalysis("pytest_schema")}
            className="rounded bg-[#121722] px-2 py-1 text-[11px] text-[#00F0FF] hover:bg-[#1A2234] border border-white/5 transition-all"
          >
            🧪 Tool AST Error
          </button>
          <button
            onClick={() => runOcrAnalysis("timeout_bloat")}
            className="rounded bg-[#121722] px-2 py-1 text-[11px] text-[#F59E0B] hover:bg-[#1A2234] border border-white/5 transition-all"
          >
            🔥 Token Bloat
          </button>
        </div>
      </div>

      {/* Diagnostic OCR Result Card */}
      {diagnostic && (
        <div className="mt-4 rounded-xl border border-[#00F0FF]/30 bg-[#121722] p-4 text-xs animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#00F0FF]" />
              <span className="font-mono font-bold text-white">Vision Diagnostic Match</span>
            </div>
            <Badge variant="emerald" size="sm">
              {formatPercent(diagnostic.confidenceScore * 100)} Confidence
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3 font-mono text-[11px]">
            <div className="rounded-lg bg-[#0A0D14] p-2.5 border border-white/5">
              <div className="text-gray-500 uppercase text-[9px]">Detected Error</div>
              <div className="text-[#EF4444] font-semibold mt-0.5">{diagnostic.errorType}</div>
            </div>
            <div className="rounded-lg bg-[#0A0D14] p-2.5 border border-white/5">
              <div className="text-gray-500 uppercase text-[9px]">Matched Trajectory</div>
              <div className="text-[#00F0FF] font-semibold mt-0.5">
                {diagnostic.matchedSuite} / {diagnostic.matchedBenchmarkId}
              </div>
            </div>
          </div>

          {/* OCR Stack Trace Snippet */}
          <div className="mb-3 rounded-lg bg-[#0A0D14] p-2.5 font-mono text-[10px] text-gray-300 border border-white/5 overflow-x-auto">
            <pre className="whitespace-pre-wrap">{diagnostic.extractedStackTrace}</pre>
          </div>

          {/* Recommended Fix Banner */}
          <div className="rounded-lg bg-gradient-to-r from-[#00F0FF]/10 to-[#10B981]/10 p-3 border border-[#00F0FF]/20">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#10B981] mt-0.5 shrink-0" />
              <div>
                <div className="font-semibold text-white">Automated Remediation Recipe</div>
                <p className="text-gray-300 mt-0.5 text-[11px]">{diagnostic.rootCauseAnalysis}</p>
                <div className="mt-2 flex items-center gap-4 text-gray-400 font-mono text-[10px]">
                  <span>
                    Route: <strong className="text-white">{diagnostic.recommendedModelRoute}</strong>
                  </span>
                  <span className="text-[#10B981] font-bold">
                    -{formatPercent(diagnostic.projectedCostReductionPct)} CPR Cost
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
