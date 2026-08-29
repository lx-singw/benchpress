"""
RFC 8785 Canonical JSON Hashing and Canonical ID Generators for Benchpress.
Guarantees byte-for-byte cross-language hash parity with TypeScript @benchpress/contracts.
"""

import hashlib
import json
from typing import Any, Dict, List
from pydantic import BaseModel


def _normalize_for_canonical_json(obj: Any) -> Any:
    """
    Recursively normalize objects for RFC 8785 canonical JSON serialization:
    - Pydantic models -> dicts
    - Floats with zero fractional part -> ints (e.g., 0.0 -> 0, 1.0 -> 1) per RFC 8785 / IEEE 754 JSON spec
    - Nested structures -> normalized
    """
    if isinstance(obj, BaseModel):
        return _normalize_for_canonical_json(obj.model_dump(mode="json"))
    if isinstance(obj, float):
        if obj.is_integer():
            return int(obj)
        return obj
    if isinstance(obj, dict):
        return {k: _normalize_for_canonical_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_for_canonical_json(item) for item in obj]
    return obj


def canonical_json_dumps(obj: Any) -> str:
    """
    Serialize obj to RFC 8785 / Canonical JSON string.
    Keys are recursively sorted in lexicographical Unicode order with compact separators and UTF-8 encoding.
    """
    normalized = _normalize_for_canonical_json(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_canonical_hash(obj: Any) -> str:
    """Compute SHA-256 hex digest of the canonical JSON representation."""
    canonical_str = canonical_json_dumps(obj)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def generate_configuration_id(payload: Dict[str, Any]) -> str:
    """Generate cfg_<sha256:16> from native configuration dictionary."""
    digest = compute_canonical_hash(payload)
    return f"cfg_{digest[:16]}"


def generate_fingerprint_id(payload: Dict[str, Any]) -> str:
    """Generate fp_<sha256:16> from fingerprint payload excluding fingerprint_id."""
    digest = compute_canonical_hash(payload)
    return f"fp_{digest[:16]}"


def generate_plan_id(payload: Dict[str, Any]) -> str:
    """Generate plan_<sha256:16> from experiment plan payload excluding plan_id."""
    digest = compute_canonical_hash(payload)
    return f"plan_{digest[:16]}"


def generate_logical_run_key(payload: Dict[str, Any]) -> str:
    """Generate run_<sha256:16> from run manifest parameters."""
    digest = compute_canonical_hash(payload)
    return f"run_{digest[:16]}"


def generate_aggregate_id(payload: Dict[str, Any]) -> str:
    """Generate agg_<sha256:16> from aggregate inputs (with sorted eligible_run_keys)."""
    eligible_keys = sorted(payload.get("eligible_run_keys", []))
    canonical_payload = {
        "experiment_id": payload["experiment_id"],
        "configuration_id": payload["configuration_id"],
        "aggregation_policy_version": payload["aggregation_policy_version"],
        "eligible_run_keys": eligible_keys,
    }
    digest = compute_canonical_hash(canonical_payload)
    return f"agg_{digest[:16]}"


def generate_receipt_id(payload_without_receipt_id: Dict[str, Any]) -> str:
    """Generate rcpt_<sha256:16> from decision receipt content."""
    clean_payload = {k: v for k, v in payload_without_receipt_id.items() if k != "receipt_id"}
    digest = compute_canonical_hash(clean_payload)
    return f"rcpt_{digest[:16]}"
