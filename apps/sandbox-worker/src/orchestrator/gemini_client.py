"""
Google GenAI SDK Client Wrapper & Telemetry Capture.
Connects to Gemini 2.5/3.5+ using google-genai SDK, capturing reasoning tokens and finish metadata.
"""

import time
import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger("benchpress.orchestrator.gemini")

@dataclass
class GeminiUsageMetadata:
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    finish_reason: str = "STOP"
    model_id: str = ""
    response_model: Optional[str] = None
    response_ids: List[str] = field(default_factory=list)


@dataclass
class GeminiCallResult:
    text: Optional[str] = None
    function_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: GeminiUsageMetadata = field(default_factory=GeminiUsageMetadata)
    raw_response: Optional[Any] = None


class GeminiOrchestratorClient:
    """Interfaces with Google GenAI SDK to invoke Gemini models with structured tools."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.default_model = default_model or settings.planner_model
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
            logger.info(f"Initialized live Google GenAI Client with model {self.default_model}")
        except Exception:
            if settings.use_local_mock:
                self.client = None
                return
            raise

    def is_live(self) -> bool:
        return self.client is not None

    def call_with_tools(
        self,
        system_instruction: str,
        contents: List[Any],
        tools: List[Any],
        model: Optional[str] = None,
    ) -> GeminiCallResult:
        """Execute a model turn with function declarations using google-genai SDK."""
        target_model = model or self.default_model
        start_time = time.perf_counter()

        if not self.client and settings.use_local_mock:
            # Fallback simulator if SDK is unavailable or in mock mode
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return GeminiCallResult(
                text="Simulated Gemini response",
                function_calls=[],
                usage=GeminiUsageMetadata(
                    prompt_tokens=450,
                    candidate_tokens=120,
                    reasoning_tokens=64,
                    total_tokens=570,
                    latency_ms=latency_ms,
                    finish_reason="STOP",
                    model_id=target_model,
                )
            )

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                tools=tools,
            )

            response = self.client.models.generate_content(
                model=target_model,
                contents=contents,
                config=config,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Extract usage metadata
            usage_meta = response.usage_metadata
            prompt_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
            candidate_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0
            # Reasoning tokens in Gemini 2.5 / 3.5+ thinking models
            reasoning_tokens = getattr(usage_meta, "thoughts_token_count", 0) or 0
            total_tokens = getattr(usage_meta, "total_token_count", prompt_tokens + candidate_tokens) or 0

            finish_reason = "STOP"
            if response.candidates and len(response.candidates) > 0:
                finish_reason = str(response.candidates[0].finish_reason)

            # Extract function calls
            function_calls = []
            if response.function_calls:
                for fc in response.function_calls:
                    function_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args) if hasattr(fc, "args") else {},
                    })

            return GeminiCallResult(
                text=response.text if hasattr(response, "text") else None,
                function_calls=function_calls,
                usage=GeminiUsageMetadata(
                    prompt_tokens=prompt_tokens,
                    candidate_tokens=candidate_tokens,
                    reasoning_tokens=reasoning_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    finish_reason=finish_reason,
                    model_id=target_model,
                    response_model=getattr(response, "model_version", None) or target_model,
                    response_ids=[getattr(response, "response_id", "")] if getattr(response, "response_id", None) else [],
                ),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Error during Gemini SDK call: {e}")
            raise
