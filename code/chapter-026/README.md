# Chapter 026 — Hybrid Search
BM25 + dense + sparse TF-IDF with RRF/weighted fusion and labeled eval.
```bash
cd code/chapter-026 && pytest -q
python3 main.py search "E-4032" --mode bm25
python3 main.py eval
python3 main.py compare "money back"
```
