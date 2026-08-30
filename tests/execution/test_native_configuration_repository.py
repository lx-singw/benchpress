from __future__ import annotations

from contracts.models import NativeConfiguration
from execution.configuration_repository import derive_configuration_id


def configuration(thinking_budget_tokens: int) -> NativeConfiguration:
    material = {
        "provider": "google",
        "request_model": "gemini-2.5-pro",
        "thinking_budget_tokens": thinking_budget_tokens,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 2048,
        "system_instruction_hash": "a" * 64,
        "tool_schema_hash": "b" * 64,
        "price_input_per_million_usd": "1.000000",
        "price_output_per_million_usd": "2.000000",
        "price_source_version": "price-v1",
        "created_at": "2026-08-29T10:00:00.000Z",
    }
    placeholder = NativeConfiguration(configuration_id="cfg_0000000000000000", **material)
    return NativeConfiguration(configuration_id=derive_configuration_id(placeholder), **material)


def test_thinking_budget_is_part_of_configuration_identity():
    without_thinking = configuration(0)
    with_thinking = configuration(2048)
    assert without_thinking.configuration_id != with_thinking.configuration_id
    assert derive_configuration_id(with_thinking) == with_thinking.configuration_id
