# Chapter 007 — Software Engineering Best Practices

`platform_core` seed: ports, adapters, DI services, factories, and pure policies.

## Setup

```bash
cd code/chapter-007
pip install pytest
```

## Run

```bash
pytest -q
python main.py describe
python main.py complete "Design a tool boundary"
```

## Layout

```text
platform_core/
  domain.py       # types
  ports.py        # Protocols
  services.py     # use cases (CompleteText)
  factories.py    # composition root
  policies.py     # pure retry decisions
  adapters/       # MockLLM, InMemoryRunRepository
  config.py
  clock.py
  errors.py
```

## Extension point (Chapter 8+)

Implement `LLMPort` for a real provider and register it in `build_llm()`:

```python
if settings.provider == "openai":
    return OpenAIAdapter(http_client, settings)
```

`CompleteText` should not change.
