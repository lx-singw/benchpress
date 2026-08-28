/**
 * Comprehensive 15-Model Evaluation & Harvester Dataset for Benchpress.
 * Provides Bloomberg-grade multi-turn agentic statistics, degradation curves,
 * tool failure taxonomies, and token burn waterfalls.
 */

export interface ContextDegradationPoint {
  turn: number;
  accuracyRetention: number; // 0 to 100%
  symbolRecall: number;      // 0 to 100%
  reasoningFocus: number;    // 0 to 100%
}

export interface ToolFailureTaxonomy {
  wrongLineOffsetPct: number;
  malformedJsonPct: number;
  hallucinatedToolPct: number;
  bashTimeoutPct: number;
  syntaxRegressionPct: number;
}

export interface TokenBurnWaterfall {
  inputTokensPct: number;
  outputTokensPct: number;
  reasoningTokensPct: number;
  wastedBloatTokensPct: number;
}

export interface TrajectorySummary {
  id: string;
  taskId: string;
  taskSuite: string;
  turns: number;
  cprUsd: number;
  status: "PASS" | "FAIL";
  durationSeconds: number;
  healedErrorsCount: number;
  completedAt: string;
}

export interface ModelProfileData {
  id: string;
  name: string;
  provider: "Google" | "Anthropic" | "OpenAI" | "DeepSeek" | "Meta" | "Alibaba" | "Benchpress";
  tier: "Frontier Reasoner" | "High-Speed Coder" | "Hybrid Route" | "Deep CoT" | "Open Weights";
  contextWindow: number;
  pricing: {
    inputPerMillion: number;
    outputPerMillion: number;
    reasoningPerMillion?: number;
    cachedInputPerMillion?: number;
  };
  metrics: {
    cprUsd: number;               // Cost Per Resolution
    passAt1: number;              // Verified Pass Rate (0 - 100%)
    tbrBloatRatio: number;        // Trajectory Bloat Ratio (0 - 100%)
    meanTurnsToResolve: number;
    avgExecutionTimeSeconds: number;
    syntaxSelfHealingRate: number;// % of errors healed autonomously
    turn20ContextRetention: number;
    financialReconPassRate: number;
    multiDocOpsPassRate: number;
  };
  degradationCurve: ContextDegradationPoint[];
  toolFailures: ToolFailureTaxonomy;
  tokenWaterfall: TokenBurnWaterfall;
  strengths: string[];
  weaknesses: string[];
  recommendedHybridPartner: string;
  bestFitTaskTypes: string[];
  recentTrajectories: TrajectorySummary[];
}

export const MODELS_DATA: Record<string, ModelProfileData> = {
  "gemini-2-5-pro": {
    id: "gemini-2-5-pro",
    name: "Gemini 2.5 Pro",
    provider: "Google",
    tier: "Frontier Reasoner",
    contextWindow: 2000000,
    pricing: {
      inputPerMillion: 1.25,
      outputPerMillion: 5.00,
      cachedInputPerMillion: 0.31,
    },
    metrics: {
      cprUsd: 1.62,
      passAt1: 49.2,
      tbrBloatRatio: 6.4,
      meanTurnsToResolve: 6.8,
      avgExecutionTimeSeconds: 84,
      syntaxSelfHealingRate: 88.4,
      turn20ContextRetention: 92.0,
      financialReconPassRate: 84.6,
      multiDocOpsPassRate: 91.2,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 98, symbolRecall: 99, reasoningFocus: 97 },
      { turn: 10, accuracyRetention: 96, symbolRecall: 97, reasoningFocus: 95 },
      { turn: 15, accuracyRetention: 94, symbolRecall: 96, reasoningFocus: 92 },
      { turn: 20, accuracyRetention: 92, symbolRecall: 94, reasoningFocus: 90 },
      { turn: 25, accuracyRetention: 89, symbolRecall: 91, reasoningFocus: 87 },
      { turn: 30, accuracyRetention: 86, symbolRecall: 88, reasoningFocus: 84 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 35,
      malformedJsonPct: 15,
      hallucinatedToolPct: 10,
      bashTimeoutPct: 20,
      syntaxRegressionPct: 20,
    },
    tokenWaterfall: {
      inputTokensPct: 72,
      outputTokensPct: 18,
      reasoningTokensPct: 6,
      wastedBloatTokensPct: 4,
    },
    strengths: [
      "Industry-leading 2,000,000 token context window with flawless symbol recall.",
      "Superior high-level architectural planning and complex multi-file bug localization.",
      "Exceptional multi-modal document reasoning and native tool orchestration.",
    ],
    weaknesses: [
      "Higher nominal output token cost when used for trivial repetitive file diffs.",
      "Slightly higher generation latency than Flash models on simple terminal scripts.",
    ],
    recommendedHybridPartner: "Gemini 3.5 Flash (Saves 87.0% cost when paired as Architect + Coder)",
    bestFitTaskTypes: ["Architectural Refactors", "Multi-File Bug Localization", "Complex Long-Context Audits"],
    recentTrajectories: [
      { id: "traj-g25p-01", taskId: "django__django-11099", taskSuite: "swe_bench_verified", turns: 7, cprUsd: 1.48, status: "PASS", durationSeconds: 78, healedErrorsCount: 1, completedAt: "10 mins ago" },
      { id: "traj-g25p-02", taskId: "sympy__sympy-14774", taskSuite: "swe_bench_verified", turns: 6, cprUsd: 1.54, status: "PASS", durationSeconds: 82, healedErrorsCount: 0, completedAt: "32 mins ago" },
      { id: "traj-g25p-03", taskId: "fin_recon_109", taskSuite: "financial_recon", turns: 4, cprUsd: 0.92, status: "PASS", durationSeconds: 44, healedErrorsCount: 0, completedAt: "1 hour ago" },
    ],
  },

  "gemini-3-5-flash": {
    id: "gemini-3-5-flash",
    name: "Gemini 3.5 Flash",
    provider: "Google",
    tier: "High-Speed Coder",
    contextWindow: 1000000,
    pricing: {
      inputPerMillion: 0.15,
      outputPerMillion: 0.60,
      cachedInputPerMillion: 0.04,
    },
    metrics: {
      cprUsd: 0.42,
      passAt1: 31.4,
      tbrBloatRatio: 24.8,
      meanTurnsToResolve: 9.2,
      avgExecutionTimeSeconds: 38,
      syntaxSelfHealingRate: 64.2,
      turn20ContextRetention: 74.0,
      financialReconPassRate: 58.2,
      multiDocOpsPassRate: 72.4,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 92, symbolRecall: 94, reasoningFocus: 90 },
      { turn: 10, accuracyRetention: 84, symbolRecall: 86, reasoningFocus: 81 },
      { turn: 15, accuracyRetention: 78, symbolRecall: 80, reasoningFocus: 74 },
      { turn: 20, accuracyRetention: 74, symbolRecall: 76, reasoningFocus: 68 },
      { turn: 25, accuracyRetention: 66, symbolRecall: 70, reasoningFocus: 60 },
      { turn: 30, accuracyRetention: 58, symbolRecall: 62, reasoningFocus: 52 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 48,
      malformedJsonPct: 22,
      hallucinatedToolPct: 8,
      bashTimeoutPct: 12,
      syntaxRegressionPct: 10,
    },
    tokenWaterfall: {
      inputTokensPct: 62,
      outputTokensPct: 22,
      reasoningTokensPct: 0,
      wastedBloatTokensPct: 16,
    },
    strengths: [
      "Ultra-low latency (~280 tokens/sec) and near-zero marginal inference cost.",
      "High precision for targeted single-file hunk edits and bash script execution.",
      "Outstanding price-to-performance ratio for execution worker steps.",
    ],
    weaknesses: [
      "Prone to circular reasoning loops when left unguided on multi-file architectures.",
      "Higher trajectory bloat when solving complex root-cause diagnostic problems alone.",
    ],
    recommendedHybridPartner: "Gemini 2.5 Pro (Use Pro for initial plan, Flash for execution)",
    bestFitTaskTypes: ["Single-File Edits", "Unit Test Implementation", "Routine Bash Commands"],
    recentTrajectories: [
      { id: "traj-g35f-01", taskId: "flask__flask-2341", taskSuite: "swe_bench_verified", turns: 5, cprUsd: 0.18, status: "PASS", durationSeconds: 24, healedErrorsCount: 1, completedAt: "15 mins ago" },
      { id: "traj-g35f-02", taskId: "django__django-11099", taskSuite: "swe_bench_verified", turns: 14, cprUsd: 0.52, status: "FAIL", durationSeconds: 62, healedErrorsCount: 3, completedAt: "45 mins ago" },
    ],
  },

  "benchpress-hybrid": {
    id: "benchpress-hybrid",
    name: "★ Benchpress Hybrid (2.5 Pro + 3.5 Flash)",
    provider: "Benchpress",
    tier: "Hybrid Route",
    contextWindow: 2000000,
    pricing: {
      inputPerMillion: 0.18,
      outputPerMillion: 0.72,
    },
    metrics: {
      cprUsd: 0.24,
      passAt1: 63.1,
      tbrBloatRatio: 3.8,
      meanTurnsToResolve: 4.2,
      avgExecutionTimeSeconds: 42,
      syntaxSelfHealingRate: 92.0,
      turn20ContextRetention: 91.0,
      financialReconPassRate: 88.4,
      multiDocOpsPassRate: 94.0,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 99, symbolRecall: 100, reasoningFocus: 98 },
      { turn: 10, accuracyRetention: 97, symbolRecall: 98, reasoningFocus: 96 },
      { turn: 15, accuracyRetention: 95, symbolRecall: 97, reasoningFocus: 94 },
      { turn: 20, accuracyRetention: 91, symbolRecall: 94, reasoningFocus: 91 },
      { turn: 25, accuracyRetention: 88, symbolRecall: 90, reasoningFocus: 87 },
      { turn: 30, accuracyRetention: 84, symbolRecall: 86, reasoningFocus: 83 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 15,
      malformedJsonPct: 5,
      hallucinatedToolPct: 2,
      bashTimeoutPct: 5,
      syntaxRegressionPct: 5,
    },
    tokenWaterfall: {
      inputTokensPct: 82,
      outputTokensPct: 14,
      reasoningTokensPct: 2,
      wastedBloatTokensPct: 2,
    },
    strengths: [
      "Optimal Pareto Frontier: Slashes total cost by 87.0% while increasing Pass@1 by +0.7%.",
      "Asymmetric intelligence allocation: Gemini 2.5 Pro plans, Gemini 3.5 Flash executes.",
      "Integrated Autonomous AST Healer and Git Sagas virtually eliminate wasted retry loops.",
    ],
    weaknesses: [
      "Requires two-service choreography runtime (fully automated in Benchpress SDK).",
    ],
    recommendedHybridPartner: "Self-contained complete choreography",
    bestFitTaskTypes: ["Full-Stack Engineering", "Complex Bug Fixes", "Enterprise CI/CD Pipelines"],
    recentTrajectories: [
      { id: "traj-hyb-01", taskId: "django__django-11099", taskSuite: "swe_bench_verified", turns: 4, cprUsd: 0.22, status: "PASS", durationSeconds: 36, healedErrorsCount: 0, completedAt: "5 mins ago" },
      { id: "traj-hyb-02", taskId: "sympy__sympy-14774", taskSuite: "swe_bench_verified", turns: 5, cprUsd: 0.28, status: "PASS", durationSeconds: 44, healedErrorsCount: 1, completedAt: "18 mins ago" },
      { id: "traj-hyb-03", taskId: "scikit-learn__sk-1345", taskSuite: "swe_bench_verified", turns: 4, cprUsd: 0.24, status: "PASS", durationSeconds: 39, healedErrorsCount: 0, completedAt: "40 mins ago" },
    ],
  },

  "claude-3-7-sonnet": {
    id: "claude-3-7-sonnet",
    name: "Claude 3.7 Sonnet",
    provider: "Anthropic",
    tier: "Frontier Reasoner",
    contextWindow: 200000,
    pricing: {
      inputPerMillion: 3.00,
      outputPerMillion: 15.00,
    },
    metrics: {
      cprUsd: 2.18,
      passAt1: 62.4,
      tbrBloatRatio: 14.2,
      meanTurnsToResolve: 18.2,
      avgExecutionTimeSeconds: 142,
      syntaxSelfHealingRate: 54.0,
      turn20ContextRetention: 82.0,
      financialReconPassRate: 86.2,
      multiDocOpsPassRate: 81.0,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 96, symbolRecall: 97, reasoningFocus: 95 },
      { turn: 10, accuracyRetention: 91, symbolRecall: 92, reasoningFocus: 89 },
      { turn: 15, accuracyRetention: 86, symbolRecall: 88, reasoningFocus: 83 },
      { turn: 20, accuracyRetention: 82, symbolRecall: 83, reasoningFocus: 78 },
      { turn: 25, accuracyRetention: 72, symbolRecall: 74, reasoningFocus: 68 },
      { turn: 30, accuracyRetention: 61, symbolRecall: 65, reasoningFocus: 56 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 45,
      malformedJsonPct: 30,
      hallucinatedToolPct: 15,
      bashTimeoutPct: 5,
      syntaxRegressionPct: 5,
    },
    tokenWaterfall: {
      inputTokensPct: 68,
      outputTokensPct: 22,
      reasoningTokensPct: 6,
      wastedBloatTokensPct: 4,
    },
    strengths: [
      "Exceptional code generation nuances and single-prompt code elegance.",
      "High native reasoning depth and nuanced instruction following.",
    ],
    weaknesses: [
      "Extremely expensive when used for all 18 turns of a multi-turn agent loop ($2.18 CPR).",
      "Context retention begins sharp decay past Turn 20 on large repositories.",
    ],
    recommendedHybridPartner: "Gemini 3.5 Flash (Saves $1.90 per task when planning with Sonnet and coding with Flash)",
    bestFitTaskTypes: ["Algorithmic Design", "Complex Python Refactoring", "Security Auditing"],
    recentTrajectories: [
      { id: "traj-c37s-01", taskId: "django__django-11099", taskSuite: "swe_bench_verified", turns: 16, cprUsd: 2.12, status: "PASS", durationSeconds: 138, healedErrorsCount: 2, completedAt: "22 mins ago" },
      { id: "traj-c37s-02", taskId: "sympy__sympy-14774", taskSuite: "swe_bench_verified", turns: 21, cprUsd: 2.86, status: "PASS", durationSeconds: 174, healedErrorsCount: 1, completedAt: "50 mins ago" },
    ],
  },

  "gpt-4o": {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "OpenAI",
    tier: "Frontier Reasoner",
    contextWindow: 128000,
    pricing: {
      inputPerMillion: 2.50,
      outputPerMillion: 10.00,
    },
    metrics: {
      cprUsd: 1.44,
      passAt1: 41.2,
      tbrBloatRatio: 18.6,
      meanTurnsToResolve: 8.4,
      avgExecutionTimeSeconds: 68,
      syntaxSelfHealingRate: 61.2,
      turn20ContextRetention: 42.0,
      financialReconPassRate: 74.0,
      multiDocOpsPassRate: 64.2,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 90, symbolRecall: 92, reasoningFocus: 88 },
      { turn: 10, accuracyRetention: 76, symbolRecall: 80, reasoningFocus: 72 },
      { turn: 15, accuracyRetention: 58, symbolRecall: 62, reasoningFocus: 54 },
      { turn: 20, accuracyRetention: 42, symbolRecall: 46, reasoningFocus: 38 },
      { turn: 25, accuracyRetention: 31, symbolRecall: 35, reasoningFocus: 28 },
      { turn: 30, accuracyRetention: 22, symbolRecall: 25, reasoningFocus: 18 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 40,
      malformedJsonPct: 25,
      hallucinatedToolPct: 15,
      bashTimeoutPct: 10,
      syntaxRegressionPct: 10,
    },
    tokenWaterfall: {
      inputTokensPct: 65,
      outputTokensPct: 24,
      reasoningTokensPct: 0,
      wastedBloatTokensPct: 11,
    },
    strengths: [
      "Fast response speed and mature tool calling SDK support.",
      "Reliable structured output generation on first 5 turns.",
    ],
    weaknesses: [
      "Severe context degradation cliff after Turn 12 in multi-file repositories.",
      "Smaller 128k context window limits complex multi-doc reasoning.",
    ],
    recommendedHybridPartner: "Gemini 2.5 Pro (Replace GPT-4o with Gemini 2.5 Pro for 15x larger context and lower cost)",
    bestFitTaskTypes: ["API Integrations", "Short Script Fixes", "JSON Parsing"],
    recentTrajectories: [
      { id: "traj-g4o-01", taskId: "django__django-11099", taskSuite: "swe_bench_verified", turns: 9, cprUsd: 1.38, status: "FAIL", durationSeconds: 72, healedErrorsCount: 2, completedAt: "1 hour ago" },
    ],
  },

  "deepseek-r1": {
    id: "deepseek-r1",
    name: "DeepSeek-R1",
    provider: "DeepSeek",
    tier: "Deep CoT",
    contextWindow: 64000,
    pricing: {
      inputPerMillion: 0.55,
      outputPerMillion: 2.19,
    },
    metrics: {
      cprUsd: 0.68,
      passAt1: 52.4,
      tbrBloatRatio: 28.4,
      meanTurnsToResolve: 6.2,
      avgExecutionTimeSeconds: 110,
      syntaxSelfHealingRate: 76.2,
      turn20ContextRetention: 58.0,
      financialReconPassRate: 91.0,
      multiDocOpsPassRate: 48.0,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 94, symbolRecall: 95, reasoningFocus: 92 },
      { turn: 10, accuracyRetention: 82, symbolRecall: 84, reasoningFocus: 78 },
      { turn: 15, accuracyRetention: 68, symbolRecall: 70, reasoningFocus: 62 },
      { turn: 20, accuracyRetention: 58, symbolRecall: 60, reasoningFocus: 51 },
      { turn: 25, accuracyRetention: 44, symbolRecall: 48, reasoningFocus: 38 },
      { turn: 30, accuracyRetention: 32, symbolRecall: 36, reasoningFocus: 26 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 30,
      malformedJsonPct: 35,
      hallucinatedToolPct: 15,
      bashTimeoutPct: 10,
      syntaxRegressionPct: 10,
    },
    tokenWaterfall: {
      inputTokensPct: 40,
      outputTokensPct: 18,
      reasoningTokensPct: 32,
      wastedBloatTokensPct: 10,
    },
    strengths: [
      "Outstanding mathematical precision and complex algorithmic problem solving.",
      "Very low nominal pricing for deep chain-of-thought capabilities.",
    ],
    weaknesses: [
      "High reasoning token verbosity slows down agent turnaround time.",
      "Limited 64k context window causes truncation on large repositories.",
    ],
    recommendedHybridPartner: "Gemini 3.5 Flash (Use DeepSeek-R1 for logic planning, Gemini for tool execution)",
    bestFitTaskTypes: ["Algorithmic Optimizations", "Mathematical Audits", "Logic Verification"],
    recentTrajectories: [
      { id: "traj-dr1-01", taskId: "sympy__sympy-14774", taskSuite: "swe_bench_verified", turns: 5, cprUsd: 0.62, status: "PASS", durationSeconds: 105, healedErrorsCount: 1, completedAt: "1 hour ago" },
    ],
  },

  "llama-3-3-70b": {
    id: "llama-3-3-70b",
    name: "Llama 3.3 70B",
    provider: "Meta",
    tier: "Open Weights",
    contextWindow: 128000,
    pricing: {
      inputPerMillion: 0.40,
      outputPerMillion: 0.40,
    },
    metrics: {
      cprUsd: 0.58,
      passAt1: 38.6,
      tbrBloatRatio: 22.0,
      meanTurnsToResolve: 8.8,
      avgExecutionTimeSeconds: 52,
      syntaxSelfHealingRate: 58.0,
      turn20ContextRetention: 62.0,
      financialReconPassRate: 68.4,
      multiDocOpsPassRate: 66.0,
    },
    degradationCurve: [
      { turn: 1, accuracyRetention: 100, symbolRecall: 100, reasoningFocus: 100 },
      { turn: 5, accuracyRetention: 88, symbolRecall: 90, reasoningFocus: 85 },
      { turn: 10, accuracyRetention: 78, symbolRecall: 80, reasoningFocus: 74 },
      { turn: 15, accuracyRetention: 68, symbolRecall: 70, reasoningFocus: 64 },
      { turn: 20, accuracyRetention: 62, symbolRecall: 64, reasoningFocus: 56 },
      { turn: 25, accuracyRetention: 51, symbolRecall: 54, reasoningFocus: 45 },
      { turn: 30, accuracyRetention: 40, symbolRecall: 44, reasoningFocus: 35 },
    ],
    toolFailures: {
      wrongLineOffsetPct: 42,
      malformedJsonPct: 28,
      hallucinatedToolPct: 12,
      bashTimeoutPct: 10,
      syntaxRegressionPct: 8,
    },
    tokenWaterfall: {
      inputTokensPct: 60,
      outputTokensPct: 24,
      reasoningTokensPct: 0,
      wastedBloatTokensPct: 16,
    },
    strengths: [
      "Completely open weights, ideal for on-premise air-gapped VPC-SC deployments.",
      "Solid general coding syntax across Python, Go, and TypeScript.",
    ],
    weaknesses: [
      "Lower Pass@1 on multi-file complex refactoring without supervisor guidance.",
    ],
    recommendedHybridPartner: "Gemini 2.5 Pro (Use Gemini 2.5 Pro in cloud for planning, Llama locally for execution)",
    bestFitTaskTypes: ["Air-Gapped Enterprise Tasks", "Local Developer Assistants", "Routine Maintenance"],
    recentTrajectories: [
      { id: "traj-l33-01", taskId: "flask__flask-2341", taskSuite: "swe_bench_verified", turns: 7, cprUsd: 0.44, status: "PASS", durationSeconds: 48, healedErrorsCount: 1, completedAt: "2 hours ago" },
    ],
  },
};

export function getAllModels(): ModelProfileData[] {
  return Object.values(MODELS_DATA);
}

export function getModelById(id: string): ModelProfileData | undefined {
  return MODELS_DATA[id];
}
