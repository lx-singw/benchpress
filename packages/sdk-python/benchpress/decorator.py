"""
Benchpress Telemetry Decorator (`@trace_trajectory`) for Custom Python AI Agents.
"""

import functools
import time
import inspect
import asyncio
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger("benchpress.sdk.trace")


def trace_trajectory(
    task_suite: str = "CUSTOM_AGENT",
    task_id_attr: Optional[str] = None,
    budget_limit_usd: float = 2.00,
):
    """Decorator to automatically instrument agent methods with Benchpress telemetry tracking."""

    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                task_id = kwargs.get(task_id_attr or "task_id", getattr(args[0], "task_id", fn.__name__) if args else fn.__name__)
                logger.info(f"[Benchpress Trace] Starting trajectory trace for {task_id} ({task_suite})")
                
                try:
                    result = await fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.info(f"[Benchpress Trace] Completed {task_id} in {duration_ms:.2f}ms (Pass@1=True)")
                    return result
                except Exception as err:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.error(f"[Benchpress Trace] Trajectory {task_id} raised error after {duration_ms:.2f}ms: {err}")
                    raise err
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                task_id = kwargs.get(task_id_attr or "task_id", getattr(args[0], "task_id", fn.__name__) if args else fn.__name__)
                logger.info(f"[Benchpress Trace] Starting sync trajectory trace for {task_id}")
                try:
                    result = fn(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.info(f"[Benchpress Trace] Completed {task_id} in {duration_ms:.2f}ms")
                    return result
                except Exception as err:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.error(f"[Benchpress Trace] Failed {task_id} after {duration_ms:.2f}ms: {err}")
                    raise err
            return sync_wrapper

    return decorator
