"""
13-State Async FSM Execution Engine with Deterministic Transitions.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .states import FsmState, TrajectoryContext, TurnResult
from supervisor.ast_healer import AstHealer
from sentinel.velocity_sentinel import VelocitySentinel
from memory.memory_bus import MemoryBus
from sandbox.runner import SandboxRunner
from telemetry.bq_streamer import BigQueryStreamer

logger = logging.getLogger("benchpress.fsm")


class AsyncFsmEngine:
    """Deterministic 13-State Finite State Machine Engine."""

    def __init__(
        self,
        context: TrajectoryContext,
        sandbox_runner: Optional[SandboxRunner] = None,
        ast_healer: Optional[AstHealer] = None,
        velocity_sentinel: Optional[VelocitySentinel] = None,
        memory_bus: Optional[MemoryBus] = None,
        bq_streamer: Optional[BigQueryStreamer] = None,
    ):
        self.ctx = context
        self.sandbox = sandbox_runner or SandboxRunner()
        self.ast_healer = ast_healer or AstHealer()
        self.sentinel = velocity_sentinel or VelocitySentinel(budget_limit_usd=context.budget_limit_usd)
        self.memory = memory_bus or MemoryBus()
        self.streamer = bq_streamer or BigQueryStreamer()

    async def transition_to(self, new_state: FsmState):
        logger.info(f"[{self.ctx.trajectory_id}] FSM Transition: {self.ctx.current_state} -> {new_state}")
        self.ctx.current_state = new_state

    async def run_trajectory(self) -> TrajectoryContext:
        """Execute full trajectory loop across FSM states."""
        try:
            # 1. State: INIT_ENVIRONMENT
            await self.transition_to(FsmState.INIT_ENVIRONMENT)
            self.ctx.workspace_path = await self.sandbox.prepare_workspace(self.ctx.task_id)

            # 2. State: FETCH_TASK
            await self.transition_to(FsmState.FETCH_TASK)
            task_data = await self.sandbox.fetch_task_fixture(self.ctx.task_suite, self.ctx.task_id)
            await self.memory.set_working_context("task_description", task_data.get("description", ""))

            # Multi-turn execution loop
            while self.ctx.current_turn < self.ctx.max_turns and not self.ctx.resolved and not self.ctx.early_halted:
                self.ctx.current_turn += 1
                turn_idx = self.ctx.current_turn

                # 3. State: PROMPT_PLANNER
                await self.transition_to(FsmState.PROMPT_PLANNER)
                turn_cost = 0.015 * (1 + turn_idx * 0.1)  # Progressive context cost model
                self.ctx.accumulated_cost_usd += turn_cost

                # 4. State: VALIDATE_AST
                await self.transition_to(FsmState.VALIDATE_AST)
                mock_tool_payload = {"tool": "edit_file", "path": "app.py", "replacement": "return True"}
                ast_valid, validation_err = self.ast_healer.validate_tool_call(mock_tool_payload)

                healed = False
                if not ast_valid:
                    # 5. State: AST_HEALING
                    await self.transition_to(FsmState.AST_HEALING)
                    mock_tool_payload, healed = await self.ast_healer.repair_payload(
                        mock_tool_payload, validation_err or "Unknown syntax error"
                    )

                # 6. State: EXECUTE_SANDBOX
                await self.transition_to(FsmState.EXECUTE_SANDBOX)
                exec_result = await self.sandbox.execute_command(
                    f"pytest tests/test_{self.ctx.task_id}.py",
                    cwd=self.ctx.workspace_path,
                )

                # 7. State: GIT_SNAPSHOT
                await self.transition_to(FsmState.GIT_SNAPSHOT)
                snapshot_hash = await self.sandbox.git_write_tree(cwd=self.ctx.workspace_path)
                self.ctx.git_snapshots.append(snapshot_hash)

                # 8. State: FINOPS_SENTINEL
                await self.transition_to(FsmState.FINOPS_SENTINEL)
                decision = self.sentinel.evaluate_turn(
                    turn_index=turn_idx,
                    accumulated_cost_usd=self.ctx.accumulated_cost_usd,
                    tokens_this_turn=2500,
                )

                turn_record = TurnResult(
                    turn_index=turn_idx,
                    state=self.ctx.current_state,
                    model_id=self.ctx.model_id,
                    prompt_tokens=2000,
                    completion_tokens=500,
                    turn_cost_usd=turn_cost,
                    latency_ms=850.0,
                    tool_call_name="edit_file",
                    tool_call_payload=mock_tool_payload,
                    ast_healed=healed,
                    sandbox_exit_code=exec_result.get("exit_code", 0),
                    sandbox_output=exec_result.get("output", ""),
                    git_tree_hash=snapshot_hash,
                )
                self.ctx.turns.append(turn_record)

                if decision.action == "EARLY_HALT":
                    self.ctx.early_halted = True
                    self.ctx.halt_reason = decision.reason
                    break

                # 9. State: EVALUATE_REWARD
                await self.transition_to(FsmState.EVALUATE_REWARD)
                if exec_result.get("exit_code") == 0:
                    self.ctx.resolved = True
                    break

                # 10. State: ROLLBACK_COMPENSATION (if sandbox failed badly)
                if exec_result.get("exit_code") == 2:
                    await self.transition_to(FsmState.ROLLBACK_COMPENSATION)
                    await self.sandbox.rollback_to_snapshot(snapshot_hash, cwd=self.ctx.workspace_path)

                # 11. State: COMPACT_MEMORY
                await self.transition_to(FsmState.COMPACT_MEMORY)
                await self.memory.compact_working_memory()

            # 12. State: FINALIZE_TELEMETRY
            await self.transition_to(FsmState.FINALIZE_TELEMETRY)
            await self.streamer.stream_trajectory_run(self.ctx)

            # 13. State: HALT_TERMINAL
            await self.transition_to(FsmState.HALT_TERMINAL)

        except Exception as e:
            logger.error(f"[{self.ctx.trajectory_id}] FSM Exception: {e}", exc_info=True)
            self.ctx.early_halted = True
            self.ctx.halt_reason = f"FSM Execution Error: {str(e)}"
            await self.transition_to(FsmState.HALT_TERMINAL)

        return self.ctx
