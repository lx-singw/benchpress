"""
Provider Adapter Interface.
Abstract base class for coding model providers (Google Gemini, Vertex AI, Anthropic, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProviderUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


@dataclass
class ProviderTurnResult:
    text: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    finish_reason: str = "STOP"
    response_model: Optional[str] = None
    response_id: Optional[str] = None


class BaseProviderAdapter(ABC):
    """Abstract interface for model execution adapters."""

    @abstractmethod
    def execute_turn(
        self,
        system_instruction: str,
        contents: List[Any],
        tools: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> ProviderTurnResult:
        """Execute a single model turn with declared tools and return structured output."""
        pass
