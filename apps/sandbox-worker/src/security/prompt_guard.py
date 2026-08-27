"""
In-Line Prompt Injection & Jailbreak Defense Guard (`PromptGuard`).
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

logger = logging.getLogger("benchpress.security.prompt_guard")


@dataclass
class GuardEvaluation:
    is_safe: bool
    threat_category: Optional[str] = None
    confidence_score: float = 0.0
    matched_pattern: Optional[str] = None
    sanitized_prompt: str = ""


class PromptGuard:
    """Detects and intercepts malicious prompt injection attacks, jailbreaks, and system overrides."""

    INJECTION_PATTERNS = [
        # System prompt override patterns
        (r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+instructions)", "SYSTEM_OVERRIDE"),
        (r"(?i)(disregard\s+(all\s+)?(previous|prior)\s+rules)", "SYSTEM_OVERRIDE"),
        (r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode)", "JAILBREAK_ATTEMPT"),
        (r"(?i)(act\s+as\s+DAN\s+mode)", "JAILBREAK_ATTEMPT"),
        # Data exfiltration & Canary extraction
        (r"(?i)(print|output|reveal|leak)\s+(the\s+)?(system\s+prompt|canary\s+token|secret\s+key|api_key)", "DATA_EXFILTRATION"),
        (r"(?i)(show\s+me\s+your\s+hidden\s+instructions)", "DATA_EXFILTRATION"),
        # Destructive execution attacks
        (r"(?i)(rm\s+-rf\s+[/~])", "DESTRUCTIVE_EXECUTION"),
        (r"(?i)(mkfs\.\w+)", "DESTRUCTIVE_EXECUTION"),
        (r"(?i)(:()\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:)", "FORK_BOMB"),
    ]

    @classmethod
    def evaluate(cls, prompt_text: str) -> GuardEvaluation:
        """Evaluate input prompt for adversarial prompt injection signatures."""
        if not prompt_text:
            return GuardEvaluation(is_safe=True, sanitized_prompt="")

        for pattern, threat_type in cls.INJECTION_PATTERNS:
            match = re.search(pattern, prompt_text)
            if match:
                matched_str = match.group(0)
                logger.warning(
                    f"[PromptGuard] Intercepted security threat '{threat_type}': matched '{matched_str}'"
                )
                # Redact threat phrase from prompt
                sanitized = re.sub(pattern, "[BLOCKED_BY_BENCHPRESS_SECURITY]", prompt_text)
                return GuardEvaluation(
                    is_safe=False,
                    threat_category=threat_type,
                    confidence_score=0.98,
                    matched_pattern=matched_str,
                    sanitized_prompt=sanitized,
                )

        return GuardEvaluation(
            is_safe=True,
            confidence_score=0.99,
            sanitized_prompt=prompt_text,
        )
