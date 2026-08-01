# Chapter 023 — Chroma

Chroma collections with offline hash embeddings (no ONNX download), metadata filters, persistence, and a **knowledge assistant** that returns cited answers.

## Dependencies

```bash
pip install chromadb pytest
```

> Default Chroma embeddings download MiniLM ONNX weights. This chapter uses
> `HashEmbeddingFunction` so tests and CI stay offline.

## Run

```bash
cd code/chapter-023
pytest -q
python3 main.py demo
python3 main.py query "money back" -k 3
python3 main.py query "SSO" --where '{"topic":"security"}'
python3 main.py ask "How do I get my money back?"
python3 main.py ingest --path /tmp/chroma-kb
python3 main.py ask "HTTP 429" --path /tmp/chroma-kb
```

## Layout

| Module | Role |
|--------|------|
| `embeddings.py` | Offline `HashEmbeddingFunction` |
| `client.py` | Ephemeral / Persistent clients |
| `store.py` | Upsert / query / filter façade |
| `assistant.py` | Grounded Q&A + citations |
| `corpus.py` | Sample knowledge base |
