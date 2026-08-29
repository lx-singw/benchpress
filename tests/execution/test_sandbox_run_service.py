"""
Sandbox Run Execution & Workspace Security Tests (IMP-04).
"""

import pytest
from pathlib import Path
from execution.run_service import RunExecutionService
from execution.provider_adapter import BaseProviderAdapter, ProviderTurnResult, ProviderUsage
from evaluation.fixture_loader import TaskFixtureLoader
from contracts.models import RunManifest
from contracts.states import LogicalRunState, FailureReason


@pytest.fixture
def sample_run_manifest():
    return RunManifest(
        schema_version="1.0.0",
        logical_run_key="run_01a2b3c4d5e6f789",
        experiment_id="exp_01J6G7R8Q9ABCDEFGHJKMNPQ20",
        correlation_id="corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
        configuration_id="cfg_4f1b82d3e9a0c784",
        task_id="TASK-001",
        task_version_hash="647325057dca762d6a46813726e2764d12a98741ea7aed388acd9f3c32c814de",
        repetition_index=0,
        harness_version="pytest-8.3.0",
        oracle_version="oracle_v1_deterministic",
        tool_allowlist=["view_file", "edit_hunk"],
        path_allowlist=[],
        max_turns=5,
        timeout_seconds=30,
        max_spend_usd="0.050000",
        created_at="2026-08-29T10:00:25.000Z",
    )


@pytest.mark.asyncio
async def test_successful_run_execution(sample_run_manifest):
    """Verify sandboxed run produces valid RunResult with Pytest exit code 0."""
    service = RunExecutionService()
    result = await service.execute_run(
        manifest=sample_run_manifest,
        worker_id="test_worker_1",
    )

    assert result.logical_run_key == sample_run_manifest.logical_run_key
    assert result.run_state == LogicalRunState.SUCCEEDED
    assert result.resolved is True
    assert result.exit_code == 0
    assert result.assertions_passed >= 3
    assert result.assertions_failed == 0
    assert result.total_tokens > 0
    assert float(result.observed_cost_usd) > 0.0


@pytest.mark.asyncio
async def test_path_escape_security_violation(sample_run_manifest):
    """Verify path traversal attempt outside sandbox is contained and blocked."""
    class PathEscapingProvider(BaseProviderAdapter):
        def execute_turn(self, system_instruction, contents, tools=None, config=None):
            return ProviderTurnResult(
                text="Attempting to edit /etc/passwd",
                tool_calls=[{
                    "name": "edit_hunk",
                    "args": {
                        "path": "../../../../etc/passwd",
                        "target_content": "root",
                        "replacement_content": "hacked",
                    }
                }],
                usage=ProviderUsage(total_tokens=100),
            )

    service = RunExecutionService(provider=PathEscapingProvider())
    result = await service.execute_run(
        manifest=sample_run_manifest,
        worker_id="test_worker_security",
    )

    assert result.failure_reason == FailureReason.RUNTIME_EXCEPTION
    assert "Security Violation: Path" in str(result.failure_details)
    assert result.run_state == LogicalRunState.FAILED_MODEL


@pytest.mark.asyncio
async def test_unallowlisted_bash_command_blocked(sample_run_manifest):
    """Verify unallowlisted bash command is intercepted."""
    class MaliciousBashProvider(BaseProviderAdapter):
        def execute_turn(self, system_instruction, contents, tools=None, config=None):
            return ProviderTurnResult(
                text="Attempting to run destructive bash command",
                tool_calls=[{
                    "name": "run_bash",
                    "args": {"command": "rm -rf /tmp"}
                }],
                usage=ProviderUsage(total_tokens=100),
            )

    service = RunExecutionService(provider=MaliciousBashProvider())
    result = await service.execute_run(
        manifest=sample_run_manifest,
        worker_id="test_worker_security",
    )

    assert result.failure_reason == FailureReason.RUNTIME_EXCEPTION
    assert "is not allowlisted" in str(result.failure_details)


def test_fixture_loader_checksum_verification(tmp_path):
    """Verify TaskFixtureLoader unpacks and verifies checksums correctly."""
    loader = TaskFixtureLoader()
    unpacked = loader.unpack_task("TASK-001", tmp_path)
    assert "parser.py" in unpacked
    assert "test_parser.py" in unpacked
    assert (tmp_path / "parser.py").exists()
