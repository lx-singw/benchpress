"""Release preflight regression tests."""

import pytest

from scripts.preflight_release import model_probe_generation_config


def test_gemini_37_probe_allows_thinking_and_visible_response():
    """The live probe cap must leave room for low thinking plus READY output."""
    pytest.importorskip("google.genai")
    config = model_probe_generation_config("gemini-3.7-flash")

    assert config.max_output_tokens == 64
    assert str(config.thinking_config.thinking_level).endswith("LOW")
