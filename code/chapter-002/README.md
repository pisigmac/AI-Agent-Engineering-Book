# Chapter 002 — The AI Engineering Roadmap

Architecture atlas for the evolving AI platform: typed stack layers, dependency validation, and placement heuristics.

## Setup

```bash
cd code/chapter-002
# optional: reuse chapter-001 logging/settings automatically if present
pip install pytest
```

## Run

```bash
python main.py map
python main.py map --mermaid
python main.py show harness
python main.py place "Research competitors and open Jira tickets"
pytest -q
```

## Layout

| File | Role |
|------|------|
| `stack_model.py` | Layer types + `StackRegistry` |
| `canonical_stack.py` | Book-canonical layer definitions |
| `placement.py` | Teaching heuristics for feature placement |
| `main.py` | CLI (`map`, `show`, `place`) |
| `tests/` | Architectural regression tests |

## How later chapters use this

When you implement a real module (tools, memory, harness, …), update the registry metadata in the same change set so docs and code stay aligned.
