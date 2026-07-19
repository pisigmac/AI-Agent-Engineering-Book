"""Tests for Chapter 7 platform_core."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from platform_core.adapters.memory_repo import InMemoryRunRepository
from platform_core.adapters.mock_llm import MockLLMAdapter
from platform_core.clock import FakeClock
from platform_core.config import Settings
from platform_core.domain import CompletionRequest
from platform_core.errors import ConfigurationError, ValidationError
from platform_core.factories import SequenceIdFactory, build_container, build_llm
from platform_core.policies import should_retry
from platform_core.services import CompleteText


def test_mock_llm_echo():
    llm = MockLLMAdapter()
    response = llm.complete(CompletionRequest(prompt="hello world", model="demo"))
    assert "hello world" in response.text
    assert response.usage_tokens >= 2


def test_mock_llm_rejects_empty_prompt():
    with pytest.raises(ValidationError):
        MockLLMAdapter().complete(CompletionRequest(prompt="   "))


def test_complete_text_persists_run():
    repo = InMemoryRunRepository()
    clock = FakeClock(now=123.0)
    ids = SequenceIdFactory()
    service = CompleteText(
        llm=MockLLMAdapter(),
        runs=repo,
        clock=clock,
        ids=ids,
        logger=logging.getLogger("test"),
        default_model="demo",
    )
    record = service("Design a tool boundary")
    assert record.run_id == "run-0001"
    assert record.created_at == 123.0
    assert repo.get("run-0001") is not None
    assert "tool boundary" in record.output


def test_fake_clock_advance():
    clock = FakeClock(now=10.0)
    clock.advance(2.5)
    assert clock.time() == 12.5


def test_build_container_mock_provider():
    container = build_container(Settings(provider="mock", default_model="demo"))
    record = container.complete_text("ping")
    assert record.output
    assert container.runs.get(record.run_id) is not None


def test_build_llm_unknown_provider():
    with pytest.raises(ConfigurationError):
        build_llm(Settings(provider="openai"))


def test_retry_policy_pure():
    assert should_retry(
        method="POST", status_code=500, idempotent=False, attempt=1
    ).retry is False
    assert should_retry(
        method="POST", status_code=429, idempotent=False, attempt=1
    ).retry is True
    assert should_retry(
        method="GET", status_code=503, idempotent=True, attempt=1
    ).retry is True
    assert should_retry(
        method="GET", status_code=503, idempotent=True, attempt=3
    ).retry is False


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    settings = Settings.from_env()
    assert settings.environment == "test"
    assert settings.provider == "mock"


def test_repository_len():
    repo = InMemoryRunRepository()
    service = CompleteText(
        llm=MockLLMAdapter(),
        runs=repo,
        clock=FakeClock(1.0),
        ids=SequenceIdFactory(),
        logger=logging.getLogger("test"),
    )
    service("one")
    service("two")
    assert len(repo) == 2


def test_service_uses_injected_model_override():
    service = CompleteText(
        llm=MockLLMAdapter(),
        runs=InMemoryRunRepository(),
        clock=FakeClock(0.0),
        ids=SequenceIdFactory(),
        logger=logging.getLogger("test"),
        default_model="default-model",
    )
    record = service("hi", model="custom-model")
    assert "[custom-model]" in record.output
