"""
Cryptographic PII & Sensitive Credential Masker (`PiiMasker`).
"""

import re
import hashlib
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("benchpress.security.pii_masker")


class PiiMasker:
    """Masks API keys, JWT tokens, private SSH keys, and emails with deterministic SHA-256 hashes."""

    CREDENTIAL_PATTERNS = [
        # Google API Key / AI Studio Key (AIzaSy...)
        (r"AIzaSy[A-Za-z0-9_-]{33}", "GCP_API_KEY"),
        # OpenAI API Key (sk-...)
        (r"sk-[A-Za-z0-9]{32,64}", "OPENAI_API_KEY"),
        # Anthropic API Key (sk-ant-...)
        (r"sk-ant-[A-Za-z0-9_-]{32,96}", "ANTHROPIC_API_KEY"),
        # Generic Bearer / JWT Token (eyJ...)
        (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "JWT_TOKEN"),
        # User Email Addresses
        (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "USER_EMAIL"),
        # RSA Private Key Header
        (r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----", "PRIVATE_KEY"),
    ]

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Replace all sensitive credentials and PII with hashed redaction tags."""
        if not text or not isinstance(text, str):
            return text

        masked = text
        for pattern, label in cls.CREDENTIAL_PATTERNS:
            def _replace_hash(match):
                raw_val = match.group(0)
                short_hash = hashlib.sha256(raw_val.encode()).hexdigest()[:8]
                return f"[{label}_REDACTED_{short_hash}]"

            masked = re.sub(pattern, _replace_hash, masked)

        return masked

    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively scrub sensitive keys and string values in dictionaries."""
        if not isinstance(data, dict):
            return data

        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                cleaned[k] = cls.mask_text(v)
            elif isinstance(v, dict):
                cleaned[k] = cls.mask_dict(v)
            elif isinstance(v, list):
                cleaned[k] = [cls.mask_text(item) if isinstance(item, str) else item for item in v]
            else:
                cleaned[k] = v

        return cleaned
