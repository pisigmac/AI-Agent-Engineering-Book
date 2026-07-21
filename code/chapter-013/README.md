# Chapter 013 — Structured Outputs

Turn messy LLM text into validated Pydantic objects with extract → validate → bounded repair.

## Setup

```bash
cd code/chapter-013
pip install pydantic pytest
```

## Run

```bash
pytest -q
python main.py extract --text '{"a":1}'
python main.py schema RouteDecision
python main.py route --message "Where is my package?"
python main.py refund --doc fixtures/order_note.txt
```

## Package

| Module | Role |
|--------|------|
| `extract.py` | JSON object extraction from fences/prose |
| `validate.py` | Pydantic validation with stable errors |
| `schema_models.py` | `RouteDecision`, `RefundAssessment` |
| `complete.py` | `StructuredCompleter` repair loop |
| `mock_llm.py` | Deterministic generator for tests |

## Integration

```python
completer = StructuredCompleter(llm.generate, max_repairs=2)
result = completer.complete(messages, RouteDecision)
if not result.ok:
    raise RuntimeError(result.error)
decision = result.value
```

Use structured completion before any side-effecting tool call.
