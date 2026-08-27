"""
Custom Enterprise Evaluation Ingestor & Task Synthesizer (`CustomEvalSynthesizer`).
Parses declarative `benchpress.eval.yaml` manifests and provisions isolated gVisor evaluation environments.
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("benchpress.evals.synthesizer")


@dataclass
class CustomEvalTask:
    task_id: str
    repo_url: str
    base_commit: str
    issue_description: str
    test_command: str
    setup_commands: List[str] = field(default_factory=list)
    budget_limit_usd: float = 1.00
    max_turns: int = 20
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class CustomEvalManifest:
    suite_name: str
    version: str
    organization: str
    tasks: List[CustomEvalTask]


class CustomEvalSynthesizer:
    """Parses and validates enterprise benchmark manifests."""

    @classmethod
    def parse_manifest_yaml(cls, yaml_content: str) -> CustomEvalManifest:
        """Parse raw YAML manifest into structured CustomEvalManifest dataclass."""
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML manifest syntax: {e}")

        if not isinstance(data, dict):
            raise ValueError("Manifest must be a YAML mapping")

        suite_name = data.get("suite_name", "enterprise_custom_suite")
        version = data.get("version", "1.0.0")
        organization = data.get("organization", "Enterprise Customer")

        raw_tasks = data.get("tasks", [])
        if not raw_tasks:
            raise ValueError("Manifest contains no tasks under 'tasks' key")

        tasks: List[CustomEvalTask] = []
        for raw in raw_tasks:
            if not raw.get("task_id") or not raw.get("test_command"):
                raise ValueError("Each task must specify 'task_id' and 'test_command'")

            task = CustomEvalTask(
                task_id=raw["task_id"],
                repo_url=raw.get("repo_url", "https://github.com/enterprise/repo.git"),
                base_commit=raw.get("base_commit", "HEAD"),
                issue_description=raw.get("issue_description", "Resolve enterprise bug"),
                test_command=raw["test_command"],
                setup_commands=raw.get("setup_commands", []),
                budget_limit_usd=float(raw.get("budget_limit_usd", 1.00)),
                max_turns=int(raw.get("max_turns", 20)),
                environment_variables=raw.get("environment_variables", {}),
            )
            tasks.append(task)

        return CustomEvalManifest(
            suite_name=suite_name,
            version=version,
            organization=organization,
            tasks=tasks,
        )

    @classmethod
    def synthesize_task_execution_context(cls, task: CustomEvalTask) -> Dict[str, Any]:
        """Synthesize runtime execution context dictionary for AsyncFSMRunner."""
        return {
            "task_id": task.task_id,
            "task_suite": "CUSTOM_ENTERPRISE",
            "repo_url": task.repo_url,
            "base_commit": task.base_commit,
            "problem_statement": task.issue_description,
            "test_cmd": task.test_command,
            "setup_cmds": task.setup_commands,
            "budget_limit_usd": task.budget_limit_usd,
            "max_turns": task.max_turns,
            "env": task.environment_variables,
        }
