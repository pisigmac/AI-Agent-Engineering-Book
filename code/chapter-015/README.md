# Chapter 015 — Embeddings

Deterministic local embedders, similarity metrics, in-memory vector index, and semantic search over a support FAQ corpus.

## Run

```bash
cd code/chapter-015
pip install pytest
pytest -q
python main.py index
python main.py search "How do I get my money back?"
python main.py similar --a "refund policy" --b "return my payment"
python main.py embed "hello world"
python main.py demo
```

## Layout

| Module | Role |
|--------|------|
| `types.py` | `Document`, `VectorRecord`, `SearchHit` |
| `normalize.py` | Unicode / whitespace policy |
| `metrics.py` | Cosine, dot, Euclidean, L2 normalize |
| `models.py` | `TfidfEmbedder` (default), `HashingEmbedder`, `BagOfWordsEmbedder` |
| `index.py` | Linear-scan top-k index |
| `pipeline.py` | Batch embed + records |
| `corpus.py` | Sample support FAQs |
| `search.py` | `SemanticSearch` service |

## Notes

- Vectors are L2-normalized; search uses dot product (= cosine).
- Default model is corpus-fitted **TF-IDF** (classic IR embedding). Hashing models are extras for pipeline tests.
- Swap in a real neural `EmbeddingModel` without changing `SearchHit` or the index API.
