# Chapter 011 — Prompt Engineering

Versioned prompt library: YAML specs, `{{var}}` rendering, pattern helpers, static CI tests.

## Setup

```bash
cd code/chapter-011
pip install pytest pyyaml
```

## Run

```bash
pytest -q
python main.py list
python main.py show support.refund
python main.py render support.refund \
  --var company=Acme \
  --var context='Refunds within 30 days with receipt.' \
  --var question='Can I refund after 45 days?'
python main.py render extract.fields --var message='Order A-1 failed payment'
python main.py test
```

## Layout

```text
promptlib/
  types.py
  template.py
  patterns.py
  registry.py
  testing.py
  library/
    support_refund_v1.yaml
    extract_fields_v1.yaml
```

## Integration

```python
from promptlib.registry import PromptRegistry, default_library_path

reg = PromptRegistry.from_directory(default_library_path())
rendered = reg.render("support.refund", {...})
messages = rendered.to_messages()
# pack with chapter-010 ContextPacker, then call LLMPort
```

Log `prompt_id` + `version` on every model call.
