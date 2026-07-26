"""JSON persistence for the offline search engine snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from searchkit.embed import HashingEmbedder, TfidfEmbedder
from searchkit.engine import SearchEngine
from searchkit.types import Document, VectorRecord


def save_engine(engine: SearchEngine, path: str | Path) -> None:
    path = Path(path)
    payload: dict[str, Any] = {
        "model": {
            "type": "tfidf" if isinstance(engine.model, TfidfEmbedder) else "hashing",
            "model_id": engine.model.model_id,
            "dimensions": engine.model.dimensions,
        },
        "documents": [
            {
                "id": d.id,
                "text": d.text,
                "title": d.title,
                "metadata": d.metadata,
            }
            for d in engine.store.all()
        ],
        "vectors": [
            {
                "id": r.id,
                "vector": list(r.vector),
                "text": r.text,
                "title": r.title,
                "metadata": r.metadata,
                "model_id": r.model_id,
                "dim": r.dim,
            }
            for r in engine.index.records()
        ],
    }
    # Persist TF-IDF vocab for exact restore
    if isinstance(engine.model, TfidfEmbedder) and engine.model.is_fitted:
        payload["model"]["vocab"] = engine.model._vocab  # noqa: SLF001
        payload["model"]["idf"] = engine.model._idf  # noqa: SLF001

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_engine(path: str | Path) -> SearchEngine:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    m = data["model"]
    if m["type"] == "tfidf":
        model = TfidfEmbedder(model_id=m["model_id"])
        if "vocab" in m and "idf" in m:
            model._vocab = {k: int(v) for k, v in m["vocab"].items()}  # noqa: SLF001
            model._idf = list(m["idf"])  # noqa: SLF001
            model.dimensions = len(model._vocab)  # noqa: SLF001
            model._fitted = True  # noqa: SLF001
    else:
        model = HashingEmbedder(dimensions=int(m["dimensions"]), model_id=m["model_id"])

    eng = SearchEngine(model=model)
    docs = [
        Document(id=d["id"], text=d["text"], title=d.get("title", ""), metadata=d.get("metadata", {}))
        for d in data["documents"]
    ]
    eng.store.upsert_many(docs)
    for v in data["vectors"]:
        eng.index.upsert(
            VectorRecord(
                id=v["id"],
                vector=tuple(v["vector"]),
                text=v["text"],
                title=v.get("title", ""),
                metadata=v.get("metadata", {}),
                model_id=v["model_id"],
                dim=v["dim"],
            )
        )
    return eng
