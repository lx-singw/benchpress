"""
Gemini Provider Adapter & Coding Tools.
Executes code edits and inspection using Google GenAI SDK with structured function calling.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from .provider_adapter import BaseProviderAdapter, ProviderTurnResult, ProviderUsage
from config import settings

logger = logging.getLogger("benchpress.execution.gemini")


def native_generation_parameters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the provider-native generation controls valid for the requested model."""
    model = str(config.get("request_model", ""))
    if model.startswith("gemini-3.7"):
        forbidden = [
            name
            for name in ("thinking_budget_tokens", "temperature", "top_p")
            if config.get(name) is not None
        ]
        if forbidden:
            raise ValueError(
                f"Gemini 3.7 configuration contains unsupported controls: {', '.join(forbidden)}"
            )
        thinking_level = str(config.get("thinking_level", "")).lower()
        if thinking_level not in {"low", "medium", "high"}:
            raise ValueError("Gemini 3.7 thinking_level must be low, medium, or high")
        return {
            "max_output_tokens": int(config["max_output_tokens"]),
            "thinking_level": thinking_level,
        }

    return {
        "temperature": float(config.get("temperature", 0.0)),
        "top_p": float(config.get("top_p", 1.0)),
        "max_output_tokens": int(config["max_output_tokens"]),
        "thinking_budget_tokens": int(config["thinking_budget_tokens"]),
    }

# Standard Coding Tools for Benchmarking Tasks
CODING_TOOLS_DECLARATIONS = [
    {
        "name": "view_file",
        "description": "View file content in sandbox workspace with line bounds.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING", "description": "Relative file path within workspace."},
                "start_line": {"type": "INTEGER", "description": "1-indexed starting line."},
                "end_line": {"type": "INTEGER", "description": "1-indexed ending line."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "edit_hunk",
        "description": "Replace a single exact target content hunk in a file with replacement content.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING", "description": "Relative file path within workspace."},
                "target_content": {"type": "STRING", "description": "Exact text chunk to replace."},
                "replacement_content": {"type": "STRING", "description": "New replacement text."}
            },
            "required": ["path", "target_content", "replacement_content"]
        }
    },
    {
        "name": "run_bash",
        "description": "Run an allowlisted non-destructive read command (ls, cat, grep, find).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {"type": "STRING", "description": "Command string to execute."}
            },
            "required": ["command"]
        }
    }
]


class GeminiProviderAdapter(BaseProviderAdapter):
    """Google GenAI SDK provider adapter for benchmark task execution."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self._init_client()

    def _init_client(self):
        if settings.use_local_mock and not self.api_key:
            return
        try:
            from google import genai

            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
            elif settings.genai_use_vertexai:
                self.client = genai.Client(
                    vertexai=True,
                    project=settings.google_cloud_project,
                    location=settings.vertex_ai_location,
                )
            else:
                raise RuntimeError("No Google GenAI authentication surface configured")
            logger.info("Initialized live Google GenAI Client for execution")
        except Exception:
            if settings.use_local_mock:
                logger.warning("Google GenAI client unavailable; retaining explicit local fixture runner")
                self.client = None
                return
            raise

    def execute_turn(
        self,
        system_instruction: str,
        contents: List[Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ProviderTurnResult:
        if not config or not config.get("request_model"):
            raise ValueError("Exact native configuration with request_model is required")
        model = str(config["request_model"])
        start_time = time.perf_counter()

        if not self.client and settings.use_local_mock:
            # Deterministic simulation runner for offline tests
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return self._mock_turn_response(contents, model, latency_ms)

        try:
            from google.genai import types

            gemini_tools = CODING_TOOLS_DECLARATIONS if tools is None else tools
            native = native_generation_parameters(config)
            generation_kwargs: Dict[str, Any] = {
                "system_instruction": system_instruction,
                "max_output_tokens": native["max_output_tokens"],
                "tools": gemini_tools,
            }
            if model.startswith("gemini-3.7"):
                generation_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_level=getattr(
                        types.ThinkingLevel,
                        str(native["thinking_level"]).upper(),
                    )
                )
            else:
                generation_kwargs.update(
                    temperature=native["temperature"],
                    top_p=native["top_p"],
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=native["thinking_budget_tokens"]
                    ),
                )

            gen_config = types.GenerateContentConfig(**generation_kwargs)

            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=gen_config,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Parse usage
            usage_meta = response.usage_metadata
            p_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
            c_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0
            r_tokens = getattr(usage_meta, "thoughts_token_count", 0) or 0
            tot_tokens = getattr(usage_meta, "total_token_count", p_tokens + c_tokens) or 0

            tool_calls = []
            if response.function_calls:
                for fc in response.function_calls:
                    tool_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args) if hasattr(fc, "args") else {},
                    })

            finish_reason = "STOP"
            if getattr(response, "candidates", None):
                finish_reason = str(response.candidates[0].finish_reason)

            return ProviderTurnResult(
                text=response.text if hasattr(response, "text") else None,
                tool_calls=tool_calls,
                usage=ProviderUsage(
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    reasoning_tokens=r_tokens,
                    cached_tokens=0,
                    total_tokens=tot_tokens,
                    latency_ms=latency_ms,
                ),
                finish_reason=finish_reason,
                response_model=getattr(response, "model_version", None) or model,
                response_id=getattr(response, "response_id", None),
            )

        except Exception as e:
            logger.error(f"GeminiProviderAdapter execution error: {e}")
            raise

    def _mock_turn_response(self, contents: List[Any], model: str, latency_ms: int) -> ProviderTurnResult:
        """Simulate model edit behaviour for offline testing."""
        # Check turn count from conversation length
        turns = len(contents)
        tool_calls = []

        if turns == 1:
            # Turn 1: view files
            tool_calls = [{"name": "view_file", "args": {"path": "security.py", "start_line": 1, "end_line": 20}}]
        elif turns == 3:
            # Turn 2: edit bug if thinking budget is active or pro model
            tool_calls = [{
                "name": "edit_hunk",
                "args": {
                    "path": "security.py",
                    "target_content": "return self.min_val <= value < self.max_val",
                    "replacement_content": "return self.min_val <= value <= self.max_val"
                }
            }]

        return ProviderTurnResult(
            text="Completed turn analysis.",
            tool_calls=tool_calls,
            usage=ProviderUsage(
                prompt_tokens=420 + (turns * 100),
                completion_tokens=150,
                reasoning_tokens=64 if "pro" in model else 0,
                cached_tokens=0,
                total_tokens=570 + (turns * 100),
                latency_ms=max(latency_ms, 120),
            ),
            finish_reason="STOP",
            response_model=model,
            response_id=None,
        )
