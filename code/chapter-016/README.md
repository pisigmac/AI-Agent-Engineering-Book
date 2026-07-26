# Chapter 016 — Model Selection

Catalog, multi-objective routing (cost / latency / quality / balanced), decision matrices, and mock completion with fallback chains.

## Run

```bash
cd code/chapter-016
pip install pytest
pytest -q
python3 main.py catalog
python3 main.py route "Classify intent: billing" --strategy cost
python3 main.py matrix "Prove multi-hop architecture trade-off carefully"
python3 main.py scores "Refactor this python class"
python3 main.py complete "hello" --fail openai:gpt-balanced
python3 main.py compare
```

## Layout

| Module | Role |
|--------|------|
| `types.py` | `ModelProfile`, `TaskRequest`, `RouteDecision` |
| `catalog.py` | Illustrative multi-provider catalog |
| `classifier.py` | Infer task kind + token estimates |
| `scoring.py` | Eligibility + weighted scores |
| `router.py` | Rank, route, fallback chain |
| `completer.py` | Routed mock completion |
| `matrix.py` | Strategy / score tables |

## Notes

- Catalog prices are **teaching fixtures**, not live vendor quotes.
- Pin real `model_id`s and load pricing from config in production.
- Open-weight local models show $0 API cost (you still pay infra).
