# Chapter 003 — Python for AI Engineers

`pyutils`: typed helpers for messages, results, text, batching, retries, and spans.

## Setup

```bash
cd code/chapter-003
pip install pytest
```

## Run

```bash
pytest -q
python main.py demo
python main.py slug "Agent Tool Registry!"
python main.py batch 2 a b c d
python main.py retry-demo
```

## Package

| Module | Contents |
|--------|----------|
| `types.py` | `Message`, `Tokenizer` protocol |
| `result.py` | `Ok` / `Err` |
| `text.py` | `clamp`, `slugify`, `truncate` |
| `iterutils.py` | `batched`, `first_n`, `sliding_window` |
| `decorators.py` | `timed`, `retry` |
| `contexts.py` | `timer_span` |
| `errors.py` | `ValidationError`, `TransientError`, `Severity` |

## Later chapters

Promote stable helpers into `platform_core` when shared across packages. Prefer importing ideas over copy-pasting.
