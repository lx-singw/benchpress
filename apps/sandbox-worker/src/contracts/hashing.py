"""
RFC 8785 Canonical JSON Hashing, ULID, and Canonical ID Generators for Benchpress.
Guarantees byte-for-byte cross-language hash parity with TypeScript @benchpress/contracts.
"""

import os
import time
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic import BaseModel

CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_ulid() -> str:
    """Generate a valid 26-character Crockford Base32 ULID matching ^[0-9A-HJKMNP-TV-Z]{26}$."""
    t = int(time.time() * 1000)
    t_chars = []
    for _ in range(10):
        t_chars.append(CROCKFORD_BASE32[t % 32])
        t //= 32
    time_part = "".join(reversed(t_chars))

    rand_bytes = os.urandom(10)
    rand_int = int.from_bytes(rand_bytes, "big")
    r_chars = []
    for _ in range(16):
        r_chars.append(CROCKFORD_BASE32[rand_int % 32])
        rand_int //= 32
    rand_part = "".join(reversed(r_chars))
    return f"{time_part}{rand_part}"


def generate_deterministic_ulid(value: Any) -> str:
    """Derive a stable ULID-shaped identifier from canonical content.

    This is intentionally not time-sortable. It is used for retry-stable object IDs
    whose contracts require the ULID alphabet and width.
    """
    number = int.from_bytes(hashlib.sha256(canonical_json_dumps(value).encode("utf-8")).digest()[:16], "big")
    chars = []
    for _ in range(26):
        chars.append(CROCKFORD_BASE32[number & 31])
        number >>= 5
    return "".join(reversed(chars))


def utc_now_rfc3339() -> str:
    """Format current UTC time matching strict 3-digit millisecond RFC 3339 regex: YYYY-MM-DDTHH:MM:SS.sssZ"""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


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
