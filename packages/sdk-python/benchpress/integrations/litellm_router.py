"""
LiteLLM and Portkey Dynamic Model Routing Middleware Hook.
Intercepts prompt requests and rewrites model target to the most cost-efficient Gemini hybrid route.
"""

import logging
from typing import Dict, Any, Optional
from ..client import SyncBenchpressClient
from ..models import TaskType, CodebaseLanguage

logger = logging.getLogger("benchpress.integrations.litellm")


class BenchpressLiteLLMRouter:
    """Drop-in dynamic model routing middleware for LiteLLM and AI gateway proxies."""

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        default_baseline_model: str = "claude-3-7-sonnet",
        cost_savings_threshold_pct: float = 50.0,
    ):
        self.client = SyncBenchpressClient(base_url=base_url, api_key=api_key)
        self.default_baseline_model = default_baseline_model
        self.cost_savings_threshold_pct = cost_savings_threshold_pct

    def route_request(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """Intercepts LiteLLM completion request and returns optimized model route."""
        # 1. Infer task type from message contents
        full_text = " ".join([m.get("content", "") for m in messages if isinstance(m.get("content"), str)])
        task_type: TaskType = "code_bug_fix"

        if "refactor" in full_text.lower() or "architect" in full_text.lower():
            task_type = "architectural_refactor"
        elif len(full_text) < 400:
            task_type = "quick_edit"

        # 2. Infer programming language
        codebase_lang: CodebaseLanguage = "python"
        if "typescript" in full_text.lower() or ".ts" in full_text.lower():
            codebase_lang = "typescript"
        elif "rust" in full_text.lower() or "cargo" in full_text.lower():
            codebase_lang = "rust"
        elif "go" in full_text.lower() or "golang" in full_text.lower():
            codebase_lang = "go"

        # 3. Query Benchpress Pareto Router
        try:
            res = self.client.get_routing_recommendation(
                task_type=task_type,
                codebase_language=codebase_lang,
                current_model=model or self.default_baseline_model,
                estimated_prompt_tokens=len(full_text) // 4,
            )

            rec = res.recommendation
            if rec.projectedSavingsPct >= self.cost_savings_threshold_pct:
                logger.info(
                    f"[BenchpressRouter] Rerouted {model} -> {rec.coderModel} "
                    f"({rec.projectedSavingsPct}% cost reduction)"
                )
                return {
                    "model": rec.coderModel,
                    "benchpress_strategy": rec.recommendedStrategy,
                    "benchpress_savings_pct": rec.projectedSavingsPct,
                    "benchpress_rationale": rec.rationale,
                }
        except Exception as e:
            logger.warning(f"[BenchpressRouter] Routing lookup failed, fallback to original model {model}: {e}")

        return {"model": model}
