"""
Schema and Model Validator Parity Tests.
Asserts that all valid contract fixtures validate under Pydantic V2 and that invalid fixtures fail closed.
"""

import json
import pytest
import sys
from pathlib import Path
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
worker_src = REPO_ROOT / "apps" / "sandbox-worker" / "src"
if str(worker_src) not in sys.path:
    sys.path.insert(0, str(worker_src))

from contracts.models import (
    ChangeEvent,
    TaskFingerprint,
    NativeConfiguration,
    ExperimentPlan,
    RunManifest,
    RunResult,
    Aggregate,
    PolicyVersion,
    CanaryResult,
    DecisionReceipt,
    ReplayEvent,
    StalenessEvent,
)

FIXTURES_VALID = REPO_ROOT / "tests" / "fixtures" / "contracts" / "valid"
FIXTURES_INVALID = REPO_ROOT / "tests" / "fixtures" / "contracts" / "invalid"

SCHEMA_MODEL_MAP = {
    "change-event.json": ChangeEvent,
    "task-fingerprint.json": TaskFingerprint,
    "native-configuration.json": NativeConfiguration,
    "experiment-plan.json": ExperimentPlan,
    "run-manifest.json": RunManifest,
    "run-result.json": RunResult,
    "aggregate.json": Aggregate,
    "policy-version.json": PolicyVersion,
    "canary-result.json": CanaryResult,
    "decision-receipt.json": DecisionReceipt,
    "replay-event.json": ReplayEvent,
    "staleness-event.json": StalenessEvent,
}


def test_all_12_valid_fixtures():
    """Verify all 12 sovereign contract valid fixtures parse cleanly with Pydantic V2 models."""
    assert len(SCHEMA_MODEL_MAP) == 12
    for fixture_name, model_cls in SCHEMA_MODEL_MAP.items():
        fixture_path = FIXTURES_VALID / fixture_name
        assert fixture_path.exists(), f"Missing valid fixture: {fixture_path}"
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Instantiate model
        instance = model_cls.model_validate(data)
        assert instance is not None
        assert instance.schema_version == "1.0.0"


def test_invalid_floating_point_currency():
    """Verify that floating point values in currency fields fail validation."""
    fixture_path = FIXTURES_INVALID / "invalid_floating_point_currency.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValidationError) as exc:
        ChangeEvent.model_validate(data)
    assert "max_spend_usd" in str(exc.value)


def test_invalid_missing_baseline():
    """Verify that missing baseline_configuration_id fails validation."""
    fixture_path = FIXTURES_INVALID / "invalid_missing_baseline.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValidationError) as exc:
        ExperimentPlan.model_validate(data)
    assert "baseline_configuration_id" in str(exc.value)


def test_invalid_negative_tokens():
    """Verify that negative token usage fails validation."""
    fixture_path = FIXTURES_INVALID / "invalid_negative_tokens.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValidationError) as exc:
        RunResult.model_validate(data)
    assert "prompt_tokens" in str(exc.value)


def test_invalid_extra_field():
    """Verify that undeclared extra fields fail closed under extra='forbid'."""
    fixture_path = FIXTURES_INVALID / "invalid_extra_field.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValidationError) as exc:
        TaskFingerprint.model_validate(data)
    assert "unauthorized_secret_field" in str(exc.value)


def test_invalid_id_format():
    """Verify that invalid ID prefix formats fail regex validation."""
    fixture_path = FIXTURES_INVALID / "invalid_id_format.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with pytest.raises(ValidationError) as exc:
        ChangeEvent.model_validate(data)
    assert "event_id" in str(exc.value)
