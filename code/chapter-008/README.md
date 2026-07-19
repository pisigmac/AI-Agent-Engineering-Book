# Chapter 008 — What is an LLM?

Offline concept lab: taxonomy, controllable mock LLM, grounded QA, and heuristic eval.

## Setup

```bash
cd code/chapter-008
pip install pytest
```

## Run

```bash
pytest -q
python main.py explain
python main.py ask "What is the refund window?"
python main.py ask "What is the refund window?" --mode hallucinate
python main.py eval-demo
```

## Layout

| Module | Role |
|--------|------|
| `taxonomy.py` | Training phases, capabilities, risks |
| `mock_llm.py` | Echo / grounded / hallucinate modes |
| `grounding.py` | In-memory docs + grounded QA |
| `eval_basic.py` | Heuristic faithfulness checks |
| `messages.py` | Chat/completion result types |

## Path to production

Replace `MockLLM` with an `LLMPort` adapter (Chapter 7) that calls a real provider via Chapter 5/6 HTTP clients. Keep grounding + eval around the model—not inside vendor SDKs only.
