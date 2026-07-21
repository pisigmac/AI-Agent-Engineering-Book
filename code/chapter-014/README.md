# Chapter 014 — Function Calling

Typed tool registry, validation, execution, and a weather-assistant tool loop.

## Run

```bash
cd code/chapter-014
pip install pydantic pytest
pytest -q
python main.py tools
python main.py weather --city Berlin
python main.py chat --message "What's the weather in Paris?"
```

## Layout

| Module | Role |
|--------|------|
| `specs.py` | `ToolSpec`, `AgentTurn`, observations |
| `registry.py` | Allowlist + schema export |
| `validate_call.py` | Name/args validation |
| `executor.py` | Timeout + structured errors |
| `loop.py` | Multi-step tool loop |
| `weather.py` | Mock weather backend |
| `mock_llm.py` | Deterministic tool-calling model |
