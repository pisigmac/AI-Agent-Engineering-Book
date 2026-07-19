# Chapter 012 — Context Engineering

Runtime context assembly: trust-aware selection, tool/memory compression, delimiter injection, and audit reports.

This package is written as real platform code—not a stub. It does not call model APIs; it decides what a model is allowed to see.

## Setup

```bash
cd code/chapter-012
pip install pytest
```

## Run

```bash
pytest -q
python main.py assemble --fixture fixtures/sample_state.json --budget 500
python main.py compare --fixture fixtures/sample_state.json
```

## Design

1. `ContextState` is the per-step snapshot (policy, goal, history, tools, memories).
2. Items are normalized with `trust`, `priority`, and recency.
3. Untrusted tool/memory payloads are capped with visible `[truncated]` markers.
4. Critical system policy is pinned; if it cannot fit, assembly fails closed.
5. Remaining budget is filled by priority then recency; survivors render in chronological order.
6. Untrusted evidence is wrapped in `UNTRUSTED_EVIDENCE` delimiters.

## Integration

```text
promptlib.render(system policy / task shell)
  → merge policy into ContextState.system_policy
  → contextkit.ContextManager.assemble(state, budget)
  → optional token_kit verification
  → LLMPort / provider HTTP
  → log AssemblyReport with the run
```

## Layout

| Path | Role |
|------|------|
| `contextkit/types.py` | State and report models |
| `contextkit/sources.py` | Snapshot → items |
| `contextkit/compress.py` | Token caps |
| `contextkit/assemble.py` | Selection algorithm |
| `contextkit/render.py` | Messages + delimiters |
| `contextkit/manager.py` | Facade |
| `fixtures/sample_state.json` | Support-agent stress fixture |
