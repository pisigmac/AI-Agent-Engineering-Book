"""Chapter 6 CLI — async HTTP and parallel request demos."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from typing import Any

from async_http import AsyncHttpClient, AsyncHttpClientError
from concurrency import map_parallel, run_in_thread
from models import ItemResult
from rate_limit_async import AsyncTokenBucket
from retry import RetryPolicy


async def _parallel_demo() -> int:
    """Offline demo: simulated delayed workers with bounded concurrency."""

    async def worker(n: int) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        if n == 2:
            raise RuntimeError("simulated failure")
        return {"n": n, "square": n * n}

    started = time.perf_counter()
    results = await map_parallel(list(range(5)), worker, concurrency=2)
    elapsed = time.perf_counter() - started
    ok = sum(1 for r in results if r.ok)
    print(
        json.dumps(
            {
                "ok": ok,
                "failed": len(results) - ok,
                "elapsed_s": round(elapsed, 3),
                "max_in_flight": getattr(map_parallel, "last_max_in_flight", None),
                "results": [r.__dict__ for r in results],
            },
            indent=2,
        )
    )
    return 0


async def _gather_urls(urls: list[str], concurrency: int) -> int:
    async with AsyncHttpClient(retry=RetryPolicy(max_attempts=2)) as client:

        async def worker(url: str) -> Any:
            return await client.get_json(url, timeout_s=20.0)

        results = await map_parallel(urls, worker, concurrency=concurrency)
    _print_results(results)
    return 0 if any(r.ok for r in results) or not urls else 1


async def _rate_limit_demo() -> int:
    bucket = AsyncTokenBucket(rate_per_s=10.0, capacity=1.0)
    started = time.perf_counter()
    await bucket.acquire()
    await bucket.acquire()
    elapsed = time.perf_counter() - started
    print(json.dumps({"elapsed_s": round(elapsed, 3), "note": "second acquire waited"}))
    return 0


async def _thread_demo() -> int:
    def blocking_square(n: int) -> int:
        time.sleep(0.05)
        return n * n

    started = time.perf_counter()
    values = await asyncio.gather(
        run_in_thread(blocking_square, 2),
        run_in_thread(blocking_square, 3),
        run_in_thread(blocking_square, 4),
    )
    elapsed = time.perf_counter() - started
    print(json.dumps({"values": values, "elapsed_s": round(elapsed, 3)}))
    return 0


def _print_results(results: list[ItemResult]) -> None:
    ok = [r for r in results if r.ok]
    bad = [r for r in results if not r.ok]
    print(
        json.dumps(
            {
                "ok_count": len(ok),
                "error_count": len(bad),
                "items": [r.__dict__ for r in results],
            },
            indent=2,
            default=str,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 6 — async toolkit CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("parallel-demo", help="Offline bounded parallel demo")
    p_urls = sub.add_parser("gather-urls", help="Fetch JSON from one or more URLs")
    p_urls.add_argument("urls", nargs="+")
    p_urls.add_argument("--concurrency", type=int, default=5)
    sub.add_parser("rate-limit-demo", help="Async token bucket demo")
    sub.add_parser("thread-demo", help="asyncio.to_thread offload demo")

    args = parser.parse_args(argv)
    if args.cmd == "parallel-demo":
        return asyncio.run(_parallel_demo())
    if args.cmd == "gather-urls":
        return asyncio.run(_gather_urls(args.urls, args.concurrency))
    if args.cmd == "rate-limit-demo":
        return asyncio.run(_rate_limit_demo())
    if args.cmd == "thread-demo":
        return asyncio.run(_thread_demo())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
