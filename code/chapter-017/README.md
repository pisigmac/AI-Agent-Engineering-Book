# Chapter 017 — Cost & Performance

Token pricing, response cache, rate limits, retries, batching, streaming usage, budgets, and a cost dashboard.

## Run

```bash
cd code/chapter-017
pip install pytest
pytest -q
python3 main.py prices
python3 main.py estimate --model openai:gpt-balanced --input 1000 --output 500
python3 main.py complete "Classify intent: billing" --repeat 3
python3 main.py dashboard
python3 main.py batch
python3 main.py stream "hello"
python3 main.py compress "Too    much     whitespace" --max-chars 40
```

## Layout

| Module | Role |
|--------|------|
| `types.py` | Usage, budget, dashboard contracts |
| `pricing.py` | Illustrative $/1M prices |
| `cache.py` | Exact response cache + savings |
| `ratelimit.py` | Dual token buckets (RPM/TPM) |
| `retry.py` | Bounded exponential backoff |
| `batch.py` | Request batching |
| `compress.py` | Prompt shrinkage heuristics |
| `stream.py` | Stream usage aggregation |
| `budget.py` | Fail-closed spend guards |
| `dashboard.py` | Aggregates + recommendations |
| `engine.py` | Wired control plane |

## Notes

- Prices are **teaching fixtures** — swap for contract rates.
- Cache keys must include model, prompt, system, temperature.
- Production: Redis cache, distributed rate limits, real provider usage fields.
