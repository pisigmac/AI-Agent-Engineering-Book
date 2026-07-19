"""Tests for Chapter 3 pyutils package."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyutils.contexts import timer_span
from pyutils.decorators import retry, timed
from pyutils.errors import TransientError, ValidationError
from pyutils.iterutils import batched, first_n, sliding_window
from pyutils.result import Err, Ok
from pyutils.text import clamp, slugify, truncate
from pyutils.types import Message, WhitespaceTokenizer


def test_clamp_and_slugify():
    assert clamp(1.5, lo=0.0, hi=1.0) == 1.0
    assert slugify("Agent Tool Registry!") == "agent-tool-registry"


def test_clamp_invalid_bounds():
    with pytest.raises(ValidationError):
        clamp(0.5, lo=1.0, hi=0.0)


def test_slugify_empty():
    with pytest.raises(ValidationError):
        slugify("   ")


def test_truncate():
    assert truncate("hello", 10) == "hello"
    assert truncate("hello world", 8).startswith("hello")
    assert len(truncate("hello world", 8)) == 8


def test_result_ok_map_and_err_unwrap():
    assert Ok(2).map(lambda x: x * 3).unwrap() == 6
    err: Err[str] = Err("nope")
    assert err.map(lambda x: x) is err
    with pytest.raises(RuntimeError):
        err.unwrap()


def test_batched_and_first_n():
    assert list(batched([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert first_n(range(10), 3) == [0, 1, 2]


def test_sliding_window():
    assert list(sliding_window([1, 2, 3, 4], 3)) == [[1, 2, 3], [2, 3, 4]]


def test_message_validation():
    msg = Message(role="user", content="hi")
    assert msg.role == "user"
    with pytest.raises(ValidationError):
        Message(role="hacker", content="x")
    with pytest.raises(ValidationError):
        Message(role="user", content="  ")


def test_tokenizer_protocol_shape():
    tok = WhitespaceTokenizer()
    assert tok.tokenize("a b  c") == ["a", "b", "c"]


def test_timed_decorator():
    @timed
    def work() -> int:
        return 7

    assert work() == 7
    assert getattr(work, "last_elapsed_s") >= 0.0


def test_retry_eventually_succeeds():
    state = {"n": 0}

    @retry(attempts=3, delay_s=0.0)
    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TransientError("no")
        return "yes"

    assert flaky() == "yes"
    assert state["n"] == 3


def test_retry_exhausted():
    @retry(attempts=2, delay_s=0.0)
    def always_fail() -> None:
        raise TransientError("still bad")

    with pytest.raises(TransientError):
        always_fail()


def test_timer_span():
    with timer_span("x") as span:
        pass
    assert span.name == "x"
    assert span.elapsed_s >= 0.0
