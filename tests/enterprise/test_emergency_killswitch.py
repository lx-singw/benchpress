"""
Enterprise Emergency Kill-Switch Test Suite.
Verifies sub-100ms operator emergency shutdown.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/sandbox-worker")))

from src.security.kill_switch import EmergencyKillSwitch


def test_emergency_killswitch_sub_100ms_execution():
    """Verify emergency killswitch triggers in < 100ms and sets global halt flag."""
    EmergencyKillSwitch.reset()
    assert EmergencyKillSwitch.check_halt() is False

    event = EmergencyKillSwitch.trigger_emergency_halt(
        operator_id="sec-admin@enterprise.com",
        reason="Compromised credential anomaly detected",
    )

    assert event.is_halted is True
    assert event.latency_ms < 100.0  # Must execute in under 100ms
    assert EmergencyKillSwitch.check_halt() is True

    # Clean up state
    EmergencyKillSwitch.reset()
    assert EmergencyKillSwitch.check_halt() is False
