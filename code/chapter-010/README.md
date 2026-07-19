# Chapter 010 — Tokens & Context Windows

Production-minded token counting, cost estimation, context packing, compression, and usage ledgers.

## Setup

```bash
cd code/chapter-010
pip install pytest
# optional exact OpenAI counts:
# pip install tiktoken
```

## Run

```bash
pytest -q
python main.py count --text "def foo():\n  return 1"
python main.py cost --model gpt-4.1 --input 1000 --output 500
python main.py pack --messages-file fixtures/sample_messages.json --budget 600
python main.py agent-report --messages-file fixtures/sample_messages.json --window 8192
python main.py list-models
```

## Package

| Module | Role |
|--------|------|
| `tokenizers.py` | `ApproxCl100kCounter`, char heuristic, optional tiktoken |
| `pricing.py` | Illustrative price table + USD estimate |
| `budget.py` | Effective input budget math |
| `compress.py` | Tool caps, sliding window, summary slot |
| `packer.py` | Priority packer with audit trail |
| `accounting.py` | Multi-step `UsageLedger` |
| `types.py` | Messages, budgets, pack results |

## Integration

Call `ContextPacker.pack(...)` immediately before `LLMPort.complete` / provider HTTP. Log `PackResult` and provider usage on every step.

Price rows are **illustrative** — replace with your contract rates.
