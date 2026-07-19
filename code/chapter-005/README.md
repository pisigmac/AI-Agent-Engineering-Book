# Chapter 005 — HTTP, APIs & JSON

Synchronous platform HTTP client: auth headers, JSON contracts, retries, rate limiting, and streaming helpers.

## Setup

```bash
cd code/chapter-005
pip install httpx pytest
```

## Offline tests

```bash
pytest -q
```

## CLI

```bash
# optional network demos
python main.py get-json https://httpbin.org/json
python main.py post-json https://httpbin.org/post '{"source":"chapter-005"}'
python main.py demo-rate-limit
python main.py show-spec
```

Environment (optional):

| Variable | Purpose |
|----------|---------|
| `API_BASE_URL` | Prefix for relative paths |
| `API_TOKEN` / `OPENAI_API_KEY` | Bearer token |
| `HTTP_RATE_PER_S` | Client token-bucket rate |

## Layout

| File | Role |
|------|------|
| `models.py` | `AuthConfig`, `RequestSpec`, `ResponseEnvelope` |
| `json_codec.py` | Strict JSON dump/load |
| `rate_limit.py` | Token bucket |
| `retry.py` | Retry/backoff policy |
| `http_client.py` | Sync client (httpx) |
| `streaming.py` | SSE / NDJSON helpers |
| `main.py` | CLI |

## Future adapter sketch

```text
OpenAIAdapter.chat()
  → builds vendor JSON body
  → HttpClient.request(RequestSpec(...))
  → maps ResponseEnvelope / stream events → platform types
```

Transport policy stays in `HttpClient`. Vendor schema stays in adapters.
