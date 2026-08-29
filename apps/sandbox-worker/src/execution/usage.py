"""
Token Usage Tracker for Model Runs.
"""

from dataclasses import dataclass


@dataclass
class AccumulatedRunUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0

    def add(self, usage):
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.reasoning_tokens += getattr(usage, "reasoning_tokens", 0)
        self.cached_tokens += getattr(usage, "cached_tokens", 0)
        self.total_tokens += usage.total_tokens
        self.latency_ms += usage.latency_ms
