# Chapter 018 — Semantic Search

Offline semantic search engine: ingest, metadata filters, cosine/MMR/boost ranking, explain, eval, JSON persistence.

## Run

```bash
cd code/chapter-018
pip install pytest
pytest -q
python3 main.py demo
python3 main.py search "How do I get my money back?" -k 3
python3 main.py search "rate limits" --topic developers
python3 main.py search "billing" --strategy mmr
python3 main.py explain "refund" kb-refund
python3 main.py eval -k 3
python3 main.py ingest --out /tmp/kb-index.json
python3 main.py search "SSO" --index /tmp/kb-index.json
```

## Layout

| Module | Role |
|--------|------|
| `embed.py` | TF-IDF / hashing embedders |
| `store.py` | Document + metadata store |
| `index.py` | Vector index + filters |
| `rank.py` | Boosts + MMR |
| `engine.py` | SearchEngine façade |
| `eval.py` | Recall@k / MRR / Precision@k |
| `persist.py` | Save/load snapshot |
| `corpus.py` | KB + labeled queries |
