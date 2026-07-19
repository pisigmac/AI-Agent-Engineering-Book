"""Tests for Chapter 1 settings bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running tests without package install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from platform_config import Settings, require_non_secret_summary


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    settings = Settings.from_env(env_file=None)
    assert settings.environment == "test"
    summary = require_non_secret_summary(settings)
    assert "openai_api_key" not in summary
    assert summary["openai_api_key_set"] == "no"


def test_api_key_flag(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")
    settings = Settings.from_env(env_file=None)
    summary = require_non_secret_summary(settings)
    assert summary["openai_api_key_set"] == "yes"
    assert "sk-test" not in str(summary)
