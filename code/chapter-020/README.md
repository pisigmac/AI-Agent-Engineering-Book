# Chapter 020 — Embedding Models

Catalog of embedding SKUs, offline teaching embedders, retrieval benchmark (Recall/MRR + multilingual), trade-off matrix, and constraint-based recommender.

## Run

```bash
cd code/chapter-020
pip install pytest
pytest -q
python3 main.py catalog
python3 main.py tradeoffs
python3 main.py bench
python3 main.py bench --models teaching:tfidf,teaching:char-ngram --english-only
python3 main.py recommend --multilingual --local
python3 main.py corpus
```

## Notes

- Commercial model cards use **illustrative** prices/dims.
- Offline bench uses teaching/proxy embedders so CI needs no API keys.
- Always re-run on **your** labeled queries before pinning a model.
