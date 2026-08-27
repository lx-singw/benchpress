"""
Closed-Loop Self-Tuning Router Test Suite.
Verifies autonomous Pareto frontier recalibration upon model weight drift or provider price drops.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))

from src.sentinel.self_tuning_router import SelfTuningRouter


def test_self_tuning_router_drift_detection_and_recalibration():
    """Verify router detects CPR drift (>10%) and autonomously recalibrates Pareto weights."""
    SelfTuningRouter.reset()
    # Canary CPR of $0.230 vs target $0.185 represents ~24.3% drift
    res = SelfTuningRouter.evaluate_drift_and_recalibrate(canary_cpr_usd=0.230)

    assert res.drift_detected is True
    assert res.cpr_delta_pct > 10.0
    assert res.webhook_dispatched is True
    assert "recalibrated_cpr_usd" in res.recalibrated_weights


def test_self_tuning_router_stable_canary_no_drift():
    """Verify router maintains steady state when drift is within normal tolerance (<10%)."""
    SelfTuningRouter.reset()
    # Canary CPR of $0.187 vs target $0.185 represents <2% drift
    res = SelfTuningRouter.evaluate_drift_and_recalibrate(
        canary_cpr_usd=0.187,
        provider_price_drop_pct=0.0,
        drift_threshold_pct=10.0,
    )

    assert res.drift_detected is False
    assert res.webhook_dispatched is False
