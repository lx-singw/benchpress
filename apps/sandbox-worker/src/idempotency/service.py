"""
Idempotency Engine & Deduplication Service.
Prevents duplicate billable provider invocations across Cloud Tasks retries using transactional CAS claims.
"""

import logging
from typing import Callable, Any, Dict, Optional
from ledger.firestore import get_ledger, ClaimStatus, ClaimResult

logger = logging.getLogger("benchpress.idempotency.service")


class IdempotencyService:
    """Manages transactional execution locks and cached response replays."""

    def __init__(self, ledger=None):
        self.ledger = ledger or get_ledger()

    async def execute_idempotent_run(
        self,
        run_key: str,
        worker_id: str,
        execution_coro: Callable[[], Any],
        lease_seconds: int = 120,
    ) -> Dict[str, Any]:
        """
        Atomically executes run with at-least-once Cloud Tasks delivery and exactly-once execution.
        """
        claim: ClaimResult = self.ledger.claim_logical_run(
            run_key=run_key,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

        if claim.status == ClaimStatus.ALREADY_COMPLETED:
            logger.info(f"[Idempotency] Run '{run_key}' already completed. Returning cached result.")
            return {
                "status": "CACHED_TERMINAL",
                "run_key": run_key,
                "result": claim.terminal_result,
                "deduplicated": True,
            }

        elif claim.status == ClaimStatus.ACTIVE_LEASE_HELD:
            logger.warning(
                f"[Idempotency] Active lease for '{run_key}' held by worker '{claim.lease_owner}' "
                f"until {claim.lease_expires_at}. Returning retryable conflict."
            )
            return {
                "status": "LEASE_HELD",
                "run_key": run_key,
                "lease_owner": claim.lease_owner,
                "retryable": True,
            }

        elif claim.status == ClaimStatus.NOT_FOUND:
            logger.error(f"[Idempotency] Run manifest for '{run_key}' not found.")
            return {
                "status": "NOT_FOUND",
                "run_key": run_key,
                "retryable": False,
            }

        # Claim Granted: execute the owned workload
        logger.info(f"[Idempotency] Lease acquired by worker '{worker_id}' for run '{run_key}'. Executing...")
        try:
            result = await execution_coro()
            # If result is a RunResult, commit to ledger
            if result:
                self.ledger.commit_terminal_result(run_key, result)
            return {
                "status": "EXECUTED",
                "run_key": run_key,
                "result": result.model_dump(mode="json") if hasattr(result, "model_dump") else result,
                "deduplicated": False,
            }
        except Exception as e:
            logger.error(f"[Idempotency] Error during execution of run '{run_key}': {e}")
            raise
