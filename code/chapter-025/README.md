# Chapter 025 — Advanced RAG / Enterprise Search

Hybrid BM25+dense (RRF), multi-query, query expansion, parent-document expansion, contextual compression, and re-ranking.

## Run

```bash
cd code/chapter-025
pip install pytest
pytest -q
python3 main.py hybrid "refund money back" --mode hybrid
python3 main.py expand "How do I get a refund?"
python3 main.py search "How do I get my money back?"
python3 main.py compare "HTTP 429 rate limit"
python3 main.py steps "password reset"
```

## Pipeline

```text
query → expand/multi-query → hybrid retrieve → RRF fuse
      → parent expand → compress → rerank → top-k
```
