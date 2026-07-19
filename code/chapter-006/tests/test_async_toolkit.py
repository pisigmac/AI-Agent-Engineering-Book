"""Offline tests for Chapter 6 async toolkit."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from async_http import AsyncHttpClient, AsyncHttpClientError
from concurrency import map_parallel, run_in_thread
from models import RequestSpec
from rate_limit_async import AsyncTokenBucket
from retry import RetryPolicy


@pytest.mark.asyncio
async def test_map_parallel_isolates_errors():
    async def worker(n: int) -> int:
        if n == 1:
            raise RuntimeError("boom")
        return n * 2

    results = await map_parallel([0, 1, 2], worker, concurrency=2)
    assert results[0].ok and results[0].value == 0
    assert not results[1].ok and "boom" in (results[1].error or "")
    assert results[2].ok and results[2].value == 4


@pytest.mark.asyncio
async def test_map_parallel_bounds_concurrency():
    current = 0
    max_seen = 0
    lock = asyncio.Lock()

    async def worker(_: int) -> str:
        nonlocal current, max_seen
        async with lock:
            current += 1
            max_seen = max(max_seen, current)
        await asyncio.sleep(0.05)
        async with lock:
            current -= 1
        return "ok"

    await map_parallel(list(range(6)), worker, concurrency=2)
    assert max_seen <= 2
    assert getattr(map_parallel, "last_max_in_flight") <= 2


@pytest.mark.asyncio
async def test_async_http_get_json_mock():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Request-ID")
        return httpx.Response(200, json={"path": request.url.path, "ok": True})

    transport = httpx.MockTransport(handler)
    async with AsyncHttpClient(
        base_url="https://example.test",
        transport=transport,
        retry=RetryPolicy(max_attempts=1),
    ) as client:
        data = await client.get_json("/v1/items")
    assert data["ok"] is True
    assert data["path"] == "/v1/items"


@pytest.mark.asyncio
async def test_async_http_retries_429():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"e": "rate"})
        return httpx.Response(200, json={"ok": True})

    async with AsyncHttpClient(
        transport=httpx.MockTransport(handler),
        retry=RetryPolicy(max_attempts=3, base_delay_s=0.0, jitter_s=0.0),
    ) as client:
        env = await client.request(
            RequestSpec(method="GET", url="https://example.test/x", idempotent=True)
        )
    assert env.status_code == 200
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_async_http_401_no_retry_loop():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"e": "nope"})

    async with AsyncHttpClient(
        transport=httpx.MockTransport(handler),
        retry=RetryPolicy(max_attempts=3),
    ) as client:
        with pytest.raises(AsyncHttpClientError) as exc:
            await client.get_json("https://example.test/secure")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_async_token_bucket_waits():
    bucket = AsyncTokenBucket(rate_per_s=20.0, capacity=1.0)
    started = time.perf_counter()
    await bucket.acquire()
    await bucket.acquire()
    assert time.perf_counter() - started >= 0.03


@pytest.mark.asyncio
async def test_run_in_thread():
    def blocking(n: int) -> int:
        return n + 1

    assert await run_in_thread(blocking, 41) == 42


@pytest.mark.asyncio
async def test_parallel_http_fanout_with_one_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/bad"):
            return httpx.Response(500, json={"e": "fail"})
        return httpx.Response(200, json={"path": request.url.path})

    transport = httpx.MockTransport(handler)

    async with AsyncHttpClient(
        transport=transport,
        retry=RetryPolicy(max_attempts=1),
    ) as client:

        async def worker(path: str):
            return await client.get_json(f"https://example.test{path}")

        results = await map_parallel(
            ["/ok", "/bad", "/also-ok"],
            worker,
            concurrency=3,
        )

    assert results[0].ok and results[0].value["path"] == "/ok"
    assert not results[1].ok
    assert results[2].ok and results[2].value["path"] == "/also-ok"
