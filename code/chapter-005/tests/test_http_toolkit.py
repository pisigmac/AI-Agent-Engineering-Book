"""Offline tests for Chapter 5 HTTP toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from http_client import HttpClient, HttpClientError
from json_codec import JsonError, dumps, loads
from models import AuthConfig, RequestSpec
from rate_limit import TokenBucket
from retry import RetryPolicy
from streaming import iter_ndjson, iter_sse_lines


def test_json_roundtrip():
    payload = {"hello": "世界", "n": 1}
    assert loads(dumps(payload)) == payload


def test_json_empty_and_invalid():
    with pytest.raises(JsonError):
        loads("")
    with pytest.raises(JsonError):
        loads("{not-json")


def test_auth_bearer_and_header():
    assert AuthConfig(kind="bearer", token="sk-test").headers()["Authorization"] == "Bearer sk-test"
    assert AuthConfig(kind="header", token="abc", header_name="x-api-key").headers()["x-api-key"] == "abc"


def test_auth_basic():
    headers = AuthConfig(kind="basic", username="u", password="p").headers()
    assert headers["Authorization"].startswith("Basic ")


def test_retry_policy_post_not_replayed_on_500():
    policy = RetryPolicy(max_attempts=3)
    assert policy.allow("POST", 500, idempotent=False, attempt=1) is False
    assert policy.allow("POST", 429, idempotent=False, attempt=1) is True
    assert policy.allow("GET", 503, idempotent=True, attempt=1) is True
    assert policy.allow("GET", 503, idempotent=True, attempt=3) is False


def test_retry_delay_honors_retry_after():
    policy = RetryPolicy(max_attempts=3, max_delay_s=10)
    assert policy.delay_s(1, retry_after_s=2.0) == 2.0


def test_token_bucket_nonblocking():
    bucket = TokenBucket(rate_per_s=100.0, capacity=1.0)
    assert bucket.acquire(1.0, block=False) == 0.0
    with pytest.raises(TimeoutError):
        bucket.acquire(1.0, block=False)


def test_sse_and_ndjson_helpers():
    lines = [": comment", "data: {\"a\":1}", "data: [DONE]", "", "junk"]
    assert list(iter_sse_lines(lines)) == ['{"a":1}', "[DONE]"]
    assert list(iter_ndjson(['{"x":1}', "", "nope", '{"y":2}'])) == [{"x": 1}, {"y": 2}]


def test_http_client_get_with_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Request-ID"]
        assert request.headers["Authorization"] == "Bearer secret"
        return httpx.Response(200, json={"ok": True, "path": request.url.path})

    transport = httpx.MockTransport(handler)
    client = HttpClient(
        base_url="https://example.test",
        auth=AuthConfig(kind="bearer", token="secret"),
        transport=transport,
        retry=RetryPolicy(max_attempts=1),
    )
    data = client.get_json("/v1/models")
    assert data["ok"] is True
    assert data["path"] == "/v1/models"


def test_http_client_retries_429_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate"})
        return httpx.Response(200, json={"ok": True})

    client = HttpClient(
        transport=httpx.MockTransport(handler),
        retry=RetryPolicy(max_attempts=3, base_delay_s=0.0, jitter_s=0.0),
    )
    env = client.request(RequestSpec(method="GET", url="https://example.test/x", idempotent=True))
    assert env.status_code == 200
    assert env.json()["ok"] is True
    assert calls["n"] == 2


def test_http_client_raises_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    client = HttpClient(
        transport=httpx.MockTransport(handler),
        retry=RetryPolicy(max_attempts=3),
    )
    with pytest.raises(HttpClientError) as exc:
        client.request(RequestSpec(method="GET", url="https://example.test/secure", idempotent=True))
    assert exc.value.status_code == 401


def test_post_json_body_encoding():
    seen: dict[str, bytes | None] = {"body": None}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content
        return httpx.Response(200, json={"echo": json.loads(request.content.decode())})

    client = HttpClient(
        transport=httpx.MockTransport(handler),
        retry=RetryPolicy(max_attempts=1),
    )
    out = client.post_json("https://example.test/post", {"hello": "platform"})
    assert out["echo"]["hello"] == "platform"
    assert seen["body"] is not None
