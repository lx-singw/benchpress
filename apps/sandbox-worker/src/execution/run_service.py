"""
Sandboxed Run Execution Service.
Coordinates isolated workspace lifecycle, path containment, provider tool turns, oracle evaluation, and RunResult persistence.
"""

import shlex
import subprocess
import time
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from contracts.models import RunManifest, RunResult
from contracts.states import LogicalRunState, FailureReason
from contracts.hashing import compute_canonical_hash, utc_now_rfc3339, generate_ulid
from .provider_adapter import BaseProviderAdapter
from .gemini_adapter import GeminiProviderAdapter
from .gemini_adapter import CODING_TOOLS_DECLARATIONS
from .configuration_repository import ConfigurationRepository, get_configuration_repository
from .usage import AccumulatedRunUsage
from .cost import calculate_observed_cost
from .failure_taxonomy import classify_run_failure
from evaluation.fixture_loader import TaskFixtureLoader
from evaluation.oracle import DeterministicPytestOracle
from ledger.firestore import get_ledger
from config import settings
from telemetry.events import workflow_events

logger = logging.getLogger("benchpress.execution.run_service")


class RunExecutionService:
    """Manages single run execution within an isolated temporary sandbox directory."""

    def __init__(
        self,
        provider: Optional[BaseProviderAdapter] = None,
        fixture_loader: Optional[TaskFixtureLoader] = None,
        oracle: Optional[DeterministicPytestOracle] = None,
        ledger = None,
        configuration_repository: Optional[ConfigurationRepository] = None,
    ):
        self.provider = provider or GeminiProviderAdapter()
        self.fixture_loader = fixture_loader or TaskFixtureLoader()
        self.oracle = oracle or DeterministicPytestOracle()
        self.ledger = ledger or get_ledger()
        self.configuration_repository = configuration_repository or get_configuration_repository()

    async def execute_run(
        self,
        manifest: RunManifest,
        worker_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> RunResult:
        """Execute task in isolated sandbox and produce immutable RunResult."""
        start_time_iso = utc_now_rfc3339()
        start_time = time.perf_counter()
        attempt_id = f"att_{generate_ulid()}"

        logger.info(
            f"[RunService] Executing run '{manifest.logical_run_key}' for task '{manifest.task_id}' "
            f"(config: {manifest.configuration_id}, attempt: {attempt_id})"
        )

        if config is not None:
            from contracts.models import NativeConfiguration

            native_configuration = NativeConfiguration.model_validate(config)
            if native_configuration.configuration_id != manifest.configuration_id:
                raise ValueError("Provided configuration does not match manifest.configuration_id")
        else:
            native_configuration = self.configuration_repository.get_configuration(manifest.configuration_id)
            if native_configuration is None:
                raise ValueError(f"Unknown immutable configuration: {manifest.configuration_id}")
        effective_config = native_configuration.model_dump(mode="json", exclude_none=True)

        accumulated_usage = AccumulatedRunUsage()
        turns_executed = 0
        tool_calls_executed = 0
        security_breach = False
        security_details = None
        provider_error = None
        budget_exceeded = False
        run_timed_out = False
        response_model = None
        provider_response_ids: List[str] = []
        max_spend = min(float(manifest.max_spend_usd), settings.per_run_spend_ceiling_usd)
        max_turns = min(manifest.max_turns, settings.max_turns)
        timeout_seconds = min(manifest.timeout_seconds, settings.per_run_timeout_seconds)
        allowed_tools = set(manifest.tool_allowlist)
        provider_tools = [tool for tool in CODING_TOOLS_DECLARATIONS if tool["name"] in allowed_tools]

        # Create isolated temporary workspace
        with tempfile.TemporaryDirectory(prefix=f"benchpress_{manifest.task_id}_") as temp_dir:
            sandbox_dir = Path(temp_dir).resolve()
            logger.debug(f"[RunService] Provisioned sandbox directory at {sandbox_dir}")

            # 1. Unpack task fixture
            try:
                self.fixture_loader.unpack_task(manifest.task_id, sandbox_dir)
            except Exception as e:
                logger.error(f"[RunService] Fixture loading failed for {manifest.task_id}: {e}")
                return self._build_infra_failure_result(
                    manifest=manifest,
                    attempt_id=attempt_id,
                    worker_id=worker_id,
                    start_time_iso=start_time_iso,
                    error_msg=f"Fixture unpack error: {str(e)}",
                )

            # 2. Prepare multi-turn tool execution loop
            system_prompt = (
                f"You are fixing a software bug in task {manifest.task_id}.\n"
                f"Inspect the code, identify the bug, and use edit_hunk to resolve failing tests."
            )
            messages: List[Any] = [{"role": "user", "parts": [{"text": "Please fix the failing tests in this repository."}]}]

            for turn in range(max_turns):
                if time.perf_counter() - start_time >= timeout_seconds:
                    run_timed_out = True
                    break
                turns_executed += 1
                try:
                    turn_res = self.provider.execute_turn(
                        system_instruction=system_prompt,
                        contents=messages,
                        tools=provider_tools,
                        config=effective_config,
                    )
                    workflow_events.emit(
                        correlation_id=manifest.correlation_id,
                        causation_id=manifest.logical_run_key,
                        object_id=attempt_id,
                        event_type="PROVIDER_CALL_COMPLETED",
                        service="sandbox-worker",
                        attempt=turn + 1,
                        details={
                            "requested_model": native_configuration.request_model,
                            "response_model": turn_res.response_model,
                            "response_id": turn_res.response_id,
                            "prompt_tokens": turn_res.usage.prompt_tokens,
                            "completion_tokens": turn_res.usage.completion_tokens,
                            "reasoning_tokens": turn_res.usage.reasoning_tokens,
                            "latency_ms": turn_res.usage.latency_ms,
                        },
                    )
                except Exception as e:
                    logger.error(f"[RunService] Provider call error on turn {turn}: {e}")
                    provider_error = str(e)
                    break

                accumulated_usage.add(turn_res.usage)
                response_model = turn_res.response_model or response_model
                if turn_res.response_id:
                    provider_response_ids.append(turn_res.response_id)
                current_cost = float(calculate_observed_cost(
                    usage=accumulated_usage,
                    price_input_per_million_usd=effective_config["price_input_per_million_usd"],
                    price_output_per_million_usd=effective_config["price_output_per_million_usd"],
                ))
                if current_cost > max_spend:
                    budget_exceeded = True
                    break

                if not turn_res.tool_calls:
                    # Model completed its turns
                    break

                # Execute tool calls in sandbox with path containment checks
                if turn_res.response_content is not None:
                    # Gemini 3.7 signs function-call parts. Preserve the exact
                    # SDK content object so opaque thought signatures survive.
                    messages.append(turn_res.response_content)
                else:
                    # Provider-neutral fallback for adapters and test doubles
                    # that do not expose a native signed response object.
                    messages.append({
                        "role": "model",
                        "parts": [
                            {
                                "function_call": {
                                    "name": tc["name"],
                                    "args": tc.get("args", {}),
                                }
                            }
                            for tc in turn_res.tool_calls
                        ],
                    })
                function_response_parts: List[Dict[str, Any]] = []
                for tc in turn_res.tool_calls:
                    name = tc["name"]
                    args = tc.get("args", {})
                    tool_calls_executed += 1
                    if tool_calls_executed > settings.max_tool_calls:
                        security_breach = True
                        security_details = "Security Violation: Maximum tool-call ceiling exceeded."
                        break
                    tool_output, is_violation = self._execute_sandbox_tool(
                        name,
                        args,
                        sandbox_dir,
                        allowed_tools,
                    )
                    workflow_events.emit(
                        correlation_id=manifest.correlation_id,
                        causation_id=attempt_id,
                        object_id=f"{attempt_id}:tool:{tool_calls_executed}",
                        event_type="TOOL_CALL_COMPLETED",
                        service="sandbox-worker",
                        attempt=tool_calls_executed,
                        severity="WARNING" if is_violation else "INFO",
                        details={
                            "tool_name": name,
                            "argument_hash": compute_canonical_hash(args),
                            "security_violation": is_violation,
                        },
                    )

                    if is_violation:
                        security_breach = True
                        security_details = tool_output
                        break

                    function_response_parts.append({
                        "function_response": {
                            "name": name,
                            # FunctionResponse.response must always be an object.
                            "response": {"result": tool_output},
                        }
                    })

                if security_breach:
                    break
                # Match the SDK's parallel function-calling conversation shape:
                # one model turn followed by one user turn with all responses.
                messages.append({
                    "role": "user",
                    "parts": function_response_parts,
                })

            if provider_error or budget_exceeded or run_timed_out or security_breach:
                oracle_res = {
                    "resolved": False,
                    "exit_code": 1,
                    "assertions_passed": 0,
                    "assertions_failed": 1,
                    "stderr": provider_error or security_details,
                    "timed_out": run_timed_out,
                }
            else:
                oracle_res = self.oracle.run_evaluation(
                    sandbox_dir=sandbox_dir,
                    timeout_seconds=timeout_seconds,
                )
            workflow_events.emit(
                correlation_id=manifest.correlation_id,
                causation_id=attempt_id,
                object_id=manifest.logical_run_key,
                event_type="ORACLE_COMPLETED",
                service="sandbox-worker",
                details={
                    "resolved": bool(oracle_res.get("resolved", False)),
                    "exit_code": int(oracle_res.get("exit_code", 1)),
                    "assertions_passed": int(oracle_res.get("assertions_passed", 0)),
                    "assertions_failed": int(oracle_res.get("assertions_failed", 0)),
                },
            )

        # 4. Finish timing and cost calculation
        finished_time_iso = utc_now_rfc3339()
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        accumulated_usage.latency_ms = latency_ms

        observed_cost = calculate_observed_cost(
            usage=accumulated_usage,
            price_input_per_million_usd=effective_config.get("price_input_per_million_usd", "1.250000"),
            price_output_per_million_usd=effective_config.get("price_output_per_million_usd", "5.000000"),
        )

        resolved = oracle_res.get("resolved", False) and not security_breach
        exit_code = oracle_res.get("exit_code", 1)
        passed_assertions = oracle_res.get("assertions_passed", 0)
        failed_assertions = oracle_res.get("assertions_failed", 0)

        failure_reason = classify_run_failure(
            exit_code=exit_code,
            assertions_failed=failed_assertions,
            timed_out=oracle_res.get("timed_out", False),
            turn_limit_exceeded=(turns_executed >= max_turns and not resolved),
            security_breach=security_breach,
            infra_error=oracle_res.get("infra_error"),
        )
        if budget_exceeded:
            failure_reason = FailureReason.BUDGET_EXCEEDED
            run_state = LogicalRunState.BUDGET_EXCEEDED
        elif run_timed_out or oracle_res.get("timed_out", False):
            failure_reason = FailureReason.TIMEOUT
            run_state = LogicalRunState.TIMED_OUT
        elif provider_error:
            failure_reason = FailureReason.PROVIDER_ERROR
            run_state = LogicalRunState.FAILED_MODEL
        elif security_breach:
            run_state = LogicalRunState.FAILED_MODEL
        elif resolved:
            run_state = LogicalRunState.SUCCEEDED
        elif oracle_res.get("infra_error"):
            run_state = LogicalRunState.FAILED_INFRA
        elif failed_assertions:
            run_state = LogicalRunState.FAILED_ORACLE
        else:
            run_state = LogicalRunState.FAILED_MODEL

        result = RunResult(
            schema_version="1.0.0",
            logical_run_key=manifest.logical_run_key,
            attempt_id=attempt_id,
            experiment_id=manifest.experiment_id,
            correlation_id=manifest.correlation_id,
            configuration_id=manifest.configuration_id,
            task_id=manifest.task_id,
            repetition_index=manifest.repetition_index,
            run_state=run_state,
            resolved=resolved,
            failure_reason=failure_reason,
            failure_details=security_details or oracle_res.get("stderr"),
            turns_executed=turns_executed,
            prompt_tokens=accumulated_usage.prompt_tokens,
            completion_tokens=accumulated_usage.completion_tokens,
            cached_tokens=accumulated_usage.cached_tokens,
            reasoning_tokens=accumulated_usage.reasoning_tokens,
            total_tokens=accumulated_usage.total_tokens,
            requested_model=native_configuration.request_model,
            response_model=response_model,
            provider_response_ids=provider_response_ids,
            observed_cost_usd=observed_cost,
            price_version=native_configuration.price_source_version,
            latency_ms=latency_ms,
            exit_code=exit_code,
            assertions_passed=passed_assertions,
            assertions_failed=failed_assertions,
            eligible_for_aggregation=True,
            lease_owner=worker_id,
            started_at=start_time_iso,
            finished_at=finished_time_iso,
            created_at=finished_time_iso,
        )

        # The idempotency owner commits this result exactly once after execution.
        logger.info(
            f"[RunService] Run '{manifest.logical_run_key}' finished: "
            f"state={run_state.value}, resolved={resolved}, cost=${observed_cost}"
        )
        return result

    def _execute_sandbox_tool(self, name: str, args: Dict[str, Any], sandbox_root: Path, allowed_tools: set[str]) -> tuple[str, bool]:
        """Execute coding tool with strict path containment checks."""
        try:
            if name not in allowed_tools:
                return f"Security Violation: Tool '{name}' is not allowlisted by the manifest.", True
            if name in {"view_file", "edit_hunk"}:
                rel_path = args.get("path", "")
                target_path = (sandbox_root / rel_path).resolve()

                # Path Containment Check
                try:
                    target_path.relative_to(sandbox_root)
                except ValueError:
                    return f"Security Violation: Path '{rel_path}' escapes sandbox root.", True

                if name == "view_file":
                    if not target_path.exists() or not target_path.is_file():
                        return f"Error: File '{rel_path}' not found.", False
                    with open(target_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    start = max(1, int(args.get("start_line", 1)))
                    end = min(len(lines), int(args.get("end_line", len(lines))))
                    content = "".join(lines[start - 1:end])
                    return content, False

                elif name == "edit_hunk":
                    if not target_path.exists() or not target_path.is_file():
                        return f"Error: Target file '{rel_path}' not found for edit.", False
                    target_content = args.get("target_content", "")
                    replacement = args.get("replacement_content", "")
                    with open(target_path, "r", encoding="utf-8") as f:
                        file_content = f.read()

                    if target_content not in file_content:
                        return f"Error: Target content not found in {rel_path}.", False

                    new_content = file_content.replace(target_content, replacement, 1)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    return f"Successfully updated {rel_path}.", False

            elif name == "run_bash":
                cmd = args.get("command", "")
                try:
                    command = shlex.split(cmd, posix=True)
                except ValueError:
                    return "Security Violation: Command could not be parsed safely.", True
                executable = command[0] if command else ""
                if executable not in {"ls", "cat", "grep", "find"}:
                    return f"Security Violation: Command '{executable}' is not allowlisted.", True
                forbidden = {"-exec", "-execdir", "-delete", "-ok", "-okdir", "-fprint", "-fprintf"}
                if any(
                    token in forbidden
                    or any(op in token for op in (";", "&&", "||", "|", "&", "`", "$(", ">", "<"))
                    for token in command
                ):
                    return "Security Violation: Shell operators or mutating find actions are prohibited.", True
                for token in command[1:]:
                    if token.startswith("-") or executable == "grep" and token == command[1]:
                        continue
                    candidate = (sandbox_root / token).resolve()
                    try:
                        candidate.relative_to(sandbox_root)
                    except ValueError:
                        return f"Security Violation: Command path '{token}' escapes sandbox root.", True
                res = subprocess.run(command, shell=False, cwd=str(sandbox_root), capture_output=True, text=True, timeout=10)
                return res.stdout or res.stderr, False

            return f"Error: Unknown tool '{name}'", False

        except Exception as e:
            return f"Tool execution error: {str(e)}", False

    def _build_infra_failure_result(
        self,
        manifest: RunManifest,
        attempt_id: str,
        worker_id: str,
        start_time_iso: str,
        error_msg: str,
    ) -> RunResult:
        now_iso = utc_now_rfc3339()
        return RunResult(
            schema_version="1.0.0",
            logical_run_key=manifest.logical_run_key,
            attempt_id=attempt_id,
            experiment_id=manifest.experiment_id,
            correlation_id=manifest.correlation_id,
            configuration_id=manifest.configuration_id,
            task_id=manifest.task_id,
            repetition_index=manifest.repetition_index,
            run_state=LogicalRunState.FAILED_INFRA,
            resolved=False,
            failure_reason=FailureReason.INFRASTRUCTURE_ERROR,
            failure_details=error_msg,
            turns_executed=0,
            prompt_tokens=0,
            completion_tokens=0,
            cached_tokens=0,
            reasoning_tokens=0,
            total_tokens=0,
            requested_model=None,
            response_model=None,
            provider_response_ids=[],
            observed_cost_usd="0.000000",
            price_version="UNAVAILABLE",
            latency_ms=0,
            exit_code=1,
            assertions_passed=0,
            assertions_failed=1,
            eligible_for_aggregation=False,
            ineligibility_reason="Worker infrastructure failure during fixture unpacking",
            lease_owner=worker_id,
            started_at=start_time_iso,
            finished_at=now_iso,
            created_at=now_iso,
        )
