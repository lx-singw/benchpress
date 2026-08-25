# Model Router Integration, SDKs & "Why Switch?" Rationale Widget

> **Document ID:** `BP-API-002`  
> **Status:** Approved / Production  
> **Target Track:** Developer Ecosystem & Multimodal UX • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Architecture: Real-Time Dynamic Model Routing

Modern AI development environments (Cursor, Windsurf, Claude Code) and routing proxies (Not Diamond, Portkey, LiteLLM) can query Benchpress to dynamically select the optimal model choreography before dispatching expensive reasoning loops.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer in IDE (Cursor / Windsurf)
    participant IDE as IDE Extension / Proxy
    participant BP as Benchpress Routing API (Cloud Run)
    participant Vertex as Vertex AI (Gemini 2.5/3.5)

    Dev->>IDE: Submits Multi-File Refactor Prompt
    IDE->>BP: POST /api/v1/routing-recommendation (Language=Python, Task=Refactor)
    BP-->>IDE: 200 OK: Route=HYBRID (Planner: Gemini 2.5 Pro, Coder: Gemini 3.5 Flash)
    
    IDE->>IDE: Display "Why Switch?" Popover (Save 87% Cost)
    IDE->>Vertex: Turn 1 -> Gemini 2.5 Pro (Planning & Task Decomposition)
    Vertex-->>IDE: Plan Strategy Checkpoints
    IDE->>Vertex: Turns 2..N -> Gemini 3.5 Flash (AST Edits & Pytest Runs)
    Vertex-->>IDE: Verified Applied Code Patch
```

---

## 2. Production Python SDK (`benchpress-python`)

```python
# File: sdk/python/benchpress/client.py
import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

class RoutingRecommendation(BaseModel):
    recommended_strategy: str
    planner_model: str
    coder_model: str
    rationale: str
    projected_cpr_usd: float
    projected_savings_pct: float
    confidence_score: float

class BenchpressClient:
    """
    Official Python SDK Client for Benchpress Intelligence Platform.
    """
    def __init__(self, api_key: str, base_url: str = "https://api.benchpress.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "benchpress-python/1.0.0"
        }

    async def get_routing_recommendation(
        self,
        task_type: str,
        codebase_language: str,
        current_model: str,
        budget_cap_usd: float = 0.50,
        accuracy_weight: float = 0.6,
        cost_weight: float = 0.4
    ) -> RoutingRecommendation:
        payload = {
            "task_type": task_type,
            "codebase_language": codebase_language,
            "current_model": current_model,
            "max_budget_per_task_usd": budget_cap_usd,
            "pareto_weights": {
                "accuracy": accuracy_weight,
                "cost": cost_weight,
                "latency": round(1.0 - accuracy_weight - cost_weight, 2)
            }
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self.base_url}/routing-recommendation",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return RoutingRecommendation(**data)
```

---

## 3. Production TypeScript SDK (`@benchpress/sdk`)

```typescript
// File: sdk/typescript/src/index.ts
export interface RoutingRequest {
  taskType: 'code_bug_fix' | 'architectural_refactor' | 'financial_extraction' | 'quick_edit';
  codebaseLanguage: string;
  currentModel: string;
  maxBudgetPerTaskUsd?: number;
  paretoWeights?: {
    accuracy: number;
    cost: number;
    latency: number;
  };
}

export interface RoutingResponse {
  recommendedStrategy: 'HYBRID_CHOREOGRAPHY' | 'MONOLITHIC_FRONTIER' | 'FAST_CODER';
  plannerModel: string;
  coderModel: string;
  rationale: string;
  projectedCprUsd: number;
  projectedSavingsPct: number;
  confidenceScore: number;
}

export class BenchpressClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl = 'https://api.benchpress.ai/api/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async getRoutingRecommendation(req: RoutingRequest): Promise<RoutingResponse> {
    const res = await fetch(`${this.baseUrl}/routing-recommendation`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': '@benchpress/sdk-ts/1.0.0',
      },
      body: JSON.stringify({
        task_type: req.taskType,
        codebase_language: req.codebaseLanguage,
        current_model: req.currentModel,
        max_budget_per_task_usd: req.maxBudgetPerTaskUsd ?? 0.50,
        pareto_weights: req.paretoWeights ?? { accuracy: 0.6, cost: 0.4, latency: 0.0 },
      }),
    });

    if (!res.ok) {
      throw new Error(`Benchpress API error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    return {
      recommendedStrategy: data.recommended_strategy,
      plannerModel: data.planner_model,
      coderModel: data.coder_model,
      rationale: data.rationale,
      projectedCprUsd: data.projected_cpr_usd,
      projectedSavingsPct: data.projected_savings_pct,
      confidenceScore: data.confidence_score,
    };
  }
}
```

---

## 4. "Why Switch?" Rationale UI Widget (React / Tailwind Component)

```tsx
// File: src/components/WhySwitchWidget.tsx
import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Zap, DollarSign } from 'lucide-react';

interface WhySwitchProps {
  currentModel: string;
  recommendedStrategy: string;
  plannerModel: string;
  coderModel: string;
  savingsPct: number;
  cprUsd: number;
  rationale: string;
  onApplyRoute: () => void;
  onDismiss: () => void;
}

export const WhySwitchWidget: React.FC<WhySwitchProps> = ({
  currentModel,
  plannerModel,
  coderModel,
  savingsPct,
  cprUsd,
  rationale,
  onApplyRoute,
  onDismiss,
}) => {
  return (
    <div className="w-full max-w-lg rounded-xl border border-white/10 bg-[#121722]/95 p-5 shadow-2xl backdrop-blur-xl transition-all duration-300">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#00F0FF]/15 text-[#00F0FF]">
            <Sparkles className="h-4 w-4" />
          </div>
          <h4 className="font-semibold text-white text-sm tracking-wide">
            BENCHPRESS MODEL ROUTER
          </h4>
        </div>
        <span className="rounded-full bg-[#10B981]/15 px-2.5 py-0.5 font-mono text-[#10B981] text-xs font-medium">
          Save {savingsPct.toFixed(1)}% Cost
        </span>
      </div>

      <div className="my-4 space-y-3">
        <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
          <span className="line-through">{currentModel}</span>
          <ArrowRight className="h-3.5 w-3.5 text-gray-500" />
          <span className="text-[#00F0FF] font-semibold">
            ★ Hybrid ({plannerModel} + {coderModel})
          </span>
        </div>

        <p className="text-xs text-gray-300 leading-relaxed bg-[#0A0D14]/80 p-3 rounded-lg border border-white/5">
          {rationale}
        </p>

        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 rounded-md bg-white/5 p-2 text-gray-300">
            <DollarSign className="h-3.5 w-3.5 text-[#10B981]" />
            <span>Target CPR: <strong>${cprUsd.toFixed(3)}</strong></span>
          </div>
          <div className="flex items-center gap-1.5 rounded-md bg-white/5 p-2 text-gray-300">
            <Zap className="h-3.5 w-3.5 text-[#00F0FF]" />
            <span>Latency: <strong>1.4s (5.8x faster)</strong></span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 pt-2">
        <button
          onClick={onDismiss}
          className="px-3 py-1.5 text-xs text-gray-400 hover:text-white transition-colors"
        >
          Dismiss
        </button>
        <button
          onClick={onApplyRoute}
          className="flex items-center gap-1.5 rounded-lg bg-[#00F0FF] px-4 py-1.5 text-xs font-medium text-black shadow-glass-cyan hover:bg-[#00F0FF]/90 transition-all"
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          Apply Recommended Route
        </button>
      </div>
    </div>
  );
};
```
