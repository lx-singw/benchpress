"""
Enterprise Canary Injection Test Suite.
Verifies dynamic canary GUID insertion and AST holdout identifier mutation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))

from src.custom_evals.canary_injector import CanaryInjector


def test_canary_guid_watermark_injection():
    """Verify CanaryInjector injects valid BENCHPRESS-CANARY-GUID header."""
    source_code = "def process_payment(amount):\n    return {'status': 'processed'}\n"
    suite_name = "acme_finance"
    task_id = "task_9901"

    res = CanaryInjector.inject_watermark_and_mutate(source_code, suite_name, task_id, mutate_holdout=False)

    assert CanaryInjector.CANARY_PREFIX in res.watermarked_content
    assert res.canary_guid in res.watermarked_content

    has_canary, detected_guid = CanaryInjector.verify_canary(res.watermarked_content)
    assert has_canary is True
    assert detected_guid == res.canary_guid


def test_canary_holdout_ast_mutations():
    """Verify holdout identifier mutation replaces targeted variables."""
    source_code = (
        "def test_settlement():\n"
        "    expected_token = 'secret_test_123'\n"
        "    user_profile_id = 9988\n"
        "    transaction_amount = 500.0\n"
        "    assert expected_token is not None\n"
    )

    res = CanaryInjector.inject_watermark_and_mutate(source_code, "acme_corp", "task_holdout_42", mutate_holdout=True)

    assert res.mutated_identifiers_count >= 3
    assert "expected_token_canary" in res.watermarked_content
    assert "user_profile_guid" in res.watermarked_content
    assert "settlement_amt_mutated" in res.watermarked_content
