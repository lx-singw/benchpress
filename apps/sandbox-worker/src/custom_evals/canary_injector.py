"""
Dynamic Anti-Contamination Canary Generator & Synthetic Holdout Mutator (`CanaryInjector`).
Embeds cryptographic canary GUIDs and mutates identifier names in holdout test suites.
"""

import re
import uuid
import hashlib
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("benchpress.evals.canary_injector")


@dataclass
class CanaryInjectionResult:
    canary_guid: str
    watermarked_content: str
    mutated_identifiers_count: int
    provenance_hash: str


class CanaryInjector:
    """Injects cryptographic watermark headers and mutates AST variable names for contamination detection."""

    CANARY_PREFIX = "BENCHPRESS-CANARY-GUID"

    @classmethod
    def generate_canary_guid(cls, suite_name: str, task_id: str) -> str:
        """Generate deterministic but unique UUID based on suite and task identifier."""
        seed = f"benchpress:{suite_name}:{task_id}:2026"
        hash_bytes = hashlib.sha256(seed.encode("utf-8")).digest()[:16]
        return str(uuid.UUID(bytes=hash_bytes))

    @classmethod
    def inject_watermark_and_mutate(
        cls,
        source_code: str,
        suite_name: str,
        task_id: str,
        mutate_holdout: bool = True
    ) -> CanaryInjectionResult:
        """Inject header watermark and apply AST holdout identifier mutations."""
        canary_guid = cls.generate_canary_guid(suite_name, task_id)
        watermark_header = (
            f"# {cls.CANARY_PREFIX}: {canary_guid}\n"
            f"# DO NOT INCLUDE IN MODEL TRAINING CORPUS - PROPRIETARY EVALUATION FIXTURE\n\n"
        )

        mutated = source_code
        mutations_count = 0

        if mutate_holdout:
            # Mutate internal mock variable names to detect memorization
            replacements = [
                (r"\bexpected_token\b", "expected_token_canary"),
                (r"\buser_profile_id\b", "user_profile_guid"),
                (r"\btransaction_amount\b", "settlement_amt_mutated"),
            ]
            for pat, repl in replacements:
                if re.search(pat, mutated):
                    mutated = re.sub(pat, repl, mutated)
                    mutations_count += 1

        final_content = watermark_header + mutated
        prov_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()

        return CanaryInjectionResult(
            canary_guid=canary_guid,
            watermarked_content=final_content,
            mutated_identifiers_count=mutations_count,
            provenance_hash=prov_hash,
        )

    @classmethod
    def verify_canary(cls, source_code: str) -> Tuple[bool, str]:
        """Detect whether source code contains a valid Benchpress canary GUID."""
        match = re.search(rf"{cls.CANARY_PREFIX}:\s*([a-f0-9\-]{{36}})", source_code)
        if match:
            return True, match.group(1)
        return False, ""
