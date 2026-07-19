# Chapter 001 — Welcome to AI Agent Engineering

Bootstrap package for the evolving AI platform.

## Setup

```bash
cd code/chapter-001
python -m pip install pydantic python-dotenv pytest
# optional:
# pip install -e ".[dev]"   # if using pyproject.toml
```

## Run

```bash
python main.py
pytest -q
```

## Layout

| File | Role |
|------|------|
| `platform_config.py` | Env-based settings (no secrets in logs) |
| `logging_setup.py` | Structured-ish logging bootstrap |
| `main.py` | CLI entrypoint |
| `tests/` | Unit tests |

## Security

- Put secrets in `.env` (gitignored at repo root)
- Never log raw API keys — use `require_non_secret_summary()`
