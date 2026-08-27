"""
Click CLI Test Suite for benchpress command-line tool.
"""

from click.testing import CliRunner
from benchpress.cli import main


def test_cli_version_flag():
    """Verify benchpress --version outputs valid semver."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "benchpress, version 1.0.0" in result.output


def test_cli_help_menu():
    """Verify benchpress --help lists route, leaderboard, and run commands."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "route" in result.output
    assert "leaderboard" in result.output
    assert "run" in result.output
