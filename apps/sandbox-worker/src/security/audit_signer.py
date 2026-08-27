"""
Cryptographic Provenance Signer (`AuditSigner`).
Signs execution trajectory events with SHA-256 HMAC for non-repudiation and enterprise audit trails.
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("benchpress.security.audit_signer")


class AuditSigner:
    """Signs trajectory audit events to ensure cryptographic provenance."""

    DEFAULT_SECRET_KEY = "benchpress-provenance-key-secret-prod-2026"

    @classmethod
    def sign_event(cls, event_data: Dict[str, Any], secret_key: str = DEFAULT_SECRET_KEY) -> str:
        """Generate deterministic HMAC-SHA256 signature for audit event payload."""
        canonical_json = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            secret_key.encode("utf-8"),
            canonical_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    @classmethod
    def verify_signature(cls, event_data: Dict[str, Any], signature: str, secret_key: str = DEFAULT_SECRET_KEY) -> bool:
        """Verify provenance of an audit event signature."""
        expected = cls.sign_event(event_data, secret_key=secret_key)
        return hmac.compare_digest(expected, signature)
