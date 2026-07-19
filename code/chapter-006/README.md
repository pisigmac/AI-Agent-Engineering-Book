# Chapter 006 — Async Python

Async HTTP client, bounded parallel map, async rate limiter, and thread offload helpers.

## Setup

```bash
cd code/chapter-006
pip install httpx pytest pytest-asyncio
```

## Run

```bash
pytest -q
python main.py parallel-demo
python main.py rate-limit-demo
python main.py thread-demo
# optional network:
python main.py gather-urls https://httpbin.org/json https://httpbin.org/uuid
```

## When to use Chapter 5 vs 6

| Situation | Prefer |
|-----------|--------|
| Single request scripts, simple tools | Sync `chapter-005` |
| Multi-tool / multi-URL fan-out | Async `chapter-006` |
| Blocking library inside async app | `run_in_thread` |

## Layout

| File | Role |
|------|------|
| `async_http.py` | `AsyncHttpClient` |
| `concurrency.py` | `map_parallel`, `gather_limited`, `run_in_thread` |
| `rate_limit_async.py` | async token bucket |
| `retry.py` | retry policy |
| `models.py` | `RequestSpec`, `ItemResult` |
