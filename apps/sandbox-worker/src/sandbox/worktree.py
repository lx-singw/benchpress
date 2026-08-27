"""
Ephemeral Worktree Provisioner & SWE-bench Task Fixture Ingestor (`django__django-11099`).
"""

import os
import shutil
import tempfile
import asyncio
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("benchpress.sandbox.worktree")

# Embedded SWE-Bench Verified Fixture: django__django-11099
DJANGO_11099_BUGGY_VALIDATORS = r'''"""
Django Core Validators (SWE-bench Verified Fixture: django__django-11099)
"""
import re

class RegexValidator:
    regex = ''
    message = 'Enter a valid value.'
    code = 'invalid'
    inverse_match = False
    flags = 0

    def __init__(self, regex=None, message=None, code=None, inverse_match=None, flags=None):
        if regex is not None:
            self.regex = regex
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if inverse_match is not None:
            self.inverse_match = inverse_match
        if flags is not None:
            self.flags = flags
        if isinstance(self.regex, str):
            self.regex = re.compile(self.regex, self.flags)

    def __call__(self, value):
        # BUG in 11099: missing regex multiline anchor boundary support in ASCII usernames
        if not self.regex.search(str(value)):
            raise ValueError(self.message)


class ASCIIUsernameValidator(RegexValidator):
    # Defective regex in buggy version (accepts invalid trailing newline)
    regex = r'^[\w.@+-]+$'
    message = 'Enter a valid username. This value may contain only English letters, numbers, and @/./+/-/_ characters.'
    flags = 0


class UnicodeUsernameValidator(RegexValidator):
    # Valid Unicode validator baseline
    regex = r'\A[\w.@+-]+\Z'
    message = 'Enter a valid username.'
    flags = 0
'''

DJANGO_11099_TEST_VALIDATORS = r'''"""
Pytest Test Suite for ASCIIUsernameValidator & UnicodeUsernameValidator.
"""
import pytest
from django.core.validators import ASCIIUsernameValidator, UnicodeUsernameValidator


def test_ascii_username_validator_valid():
    validator = ASCIIUsernameValidator()
    validator("valid_user.123@example")
    assert True


def test_ascii_username_validator_rejects_trailing_newline():
    validator = ASCIIUsernameValidator()
    # Trailing newline must be rejected by corrected regex \A[\w.@+-]+\Z
    with pytest.raises(ValueError):
        validator("invalid_user\n")


def test_unicode_username_validator_rejects_trailing_newline():
    validator = UnicodeUsernameValidator()
    with pytest.raises(ValueError):
        validator("unicode_user\n")
'''


class EphemeralWorktreeProvisioner:
    """Manages creation, git-initialization, and fixture loading for ephemeral test sandboxes."""

    @classmethod
    async def provision_task_worktree(cls, task_suite: str, task_id: str) -> str:
        """Create and populate isolated git repository for a benchmark task."""
        temp_dir = tempfile.mkdtemp(prefix=f"benchpress_{task_id}_")
        logger.info(f"[Worktree] Provisioning ephemeral workspace at {temp_dir}")

        # 1. Initialize git repo
        await (await asyncio.create_subprocess_exec("git", "init", cwd=temp_dir)).wait()
        await (await asyncio.create_subprocess_exec("git", "config", "user.name", "BenchpressBot", cwd=temp_dir)).wait()
        await (await asyncio.create_subprocess_exec("git", "config", "user.email", "bot@benchpress.ai", cwd=temp_dir)).wait()

        # 2. Populate task files
        if "11099" in task_id or "django" in task_id.lower():
            pkg_dir = os.path.join(temp_dir, "django", "core")
            test_dir = os.path.join(temp_dir, "tests")
            os.makedirs(pkg_dir, exist_ok=True)
            os.makedirs(test_dir, exist_ok=True)

            with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
                f.write("")
            with open(os.path.join(pkg_dir, "validators.py"), "w") as f:
                f.write(DJANGO_11099_BUGGY_VALIDATORS)
            with open(os.path.join(test_dir, "test_validators.py"), "w") as f:
                f.write(DJANGO_11099_TEST_VALIDATORS)
            with open(os.path.join(temp_dir, "setup.py"), "w") as f:
                f.write("from setuptools import setup, find_packages\nsetup(name='django', packages=find_packages())\n")
        else:
            # Generic default task fixture
            src_dir = os.path.join(temp_dir, "src")
            test_dir = os.path.join(temp_dir, "tests")
            os.makedirs(src_dir, exist_ok=True)
            os.makedirs(test_dir, exist_ok=True)

            with open(os.path.join(src_dir, "app.py"), "w") as f:
                f.write("def resolve_query():\n    return False\n")
            with open(os.path.join(test_dir, "test_app.py"), "w") as f:
                f.write("import pytest\nfrom src.app import resolve_query\ndef test_query():\n    assert resolve_query() is True\n")

        # 3. Initial Git Commit
        await (await asyncio.create_subprocess_exec("git", "add", "-A", cwd=temp_dir)).wait()
        await (await asyncio.create_subprocess_exec("git", "commit", "-m", f"Initial SWE-bench fixture: {task_id}", cwd=temp_dir)).wait()

        return temp_dir

    @classmethod
    async def cleanup_worktree(cls, worktree_dir: str):
        """Teardown ephemeral directory."""
        if os.path.exists(worktree_dir):
            try:
                shutil.rmtree(worktree_dir, ignore_errors=True)
                logger.info(f"[Worktree] Cleaned up workspace {worktree_dir}")
            except Exception as e:
                logger.warning(f"[Worktree] Cleanup warning: {e}")
