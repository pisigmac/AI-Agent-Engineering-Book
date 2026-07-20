"""Tests for function-calling runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from toolcall.executor import ToolExecutor
from toolcall.loop import ToolLoop, build_weather_registry, weather_assistant
from toolcall.mock_llm import MockToolLLM
from toolcall.validate_call import ToolCallValidationError, validate_tool_arguments
from toolcall.weather import get_weather


def test_registry_and_schemas():
    reg = build_weather_registry()
    assert "get_weather" in reg.list()
    schemas = reg.export_schemas()
    assert any(s["name"] == "get_weather" for s in schemas)


def test_validate_args_and_unknown_tool():
    reg = build_weather_registry()
    args = validate_tool_arguments(reg, "get_weather", {"city": "Berlin", "units": "metric"})
    assert args.city == "Berlin"
    with pytest.raises(ToolCallValidationError) as exc:
        validate_tool_arguments(reg, "nope", {})
    assert exc.value.code == "unknown_tool"


def test_executor_success_and_business_error():
    reg = build_weather_registry()
    ex = ToolExecutor(reg)
    ok = ex.execute("get_weather", {"city": "Paris", "units": "metric"})
    assert ok.ok and ok.result["condition"]
    bad = ex.execute("get_weather", {"city": "Atlantis", "units": "metric"})
    assert not bad.ok and bad.error_code == "execution_error"


def test_weather_handler_units():
    metric = get_weather("Berlin", "metric")
    imperial = get_weather("Berlin", "imperial")
    assert metric["units"] == "C"
    assert imperial["units"] == "F"


def test_loop_tool_then_final():
    result = weather_assistant("What's the weather in Berlin?")
    assert result.ok
    assert result.stop_reason == "final"
    assert any(s.get("kind") == "tool" for s in result.steps)
    assert "Berlin" in result.final_message or "berlin" in result.final_message.lower()
    # Should mention temperature from tool path
    assert "°" in result.final_message or "source" in result.final_message.lower()


def test_loop_unsupported_city_recovers():
    result = weather_assistant("Weather in Atlantis?")
    # tool fails then final explains
    assert any(s.get("kind") == "tool" for s in result.steps)
    assert result.final_message


def test_observation_is_delimited():
    reg = build_weather_registry()
    obs = ToolExecutor(reg).execute("get_weather", {"city": "Tokyo"})
    content = obs.to_message_content()
    assert "UNTRUSTED_EVIDENCE" in content
    assert "get_weather" in content
