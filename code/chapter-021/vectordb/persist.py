"""JSON persistence for the mini vector database."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vectordb.collection import Collection
from vectordb.database import VectorDB
from vectordb.types import VectorRecord


def save_db(db: VectorDB, path: str | Path) -> None:
    path = Path(path)
    payload: dict[str, Any] = {"collections": {}}
    for name in db.list_collections():
        col = db.get_collection(name)
        st = col.stats()
        payload["collections"][name] = {
            "index_type": col.index_type,
            "dimensions": st.dimensions,
            "model_id": col.model_id,
            "records": [
                {
                    "id": r.id,
                    "vector": list(r.vector),
                    "metadata": r.metadata,
                    "text": r.text,
                }
                for r in col._index.records()  # noqa: SLF001
            ],
        }
        if col.index_type == "ivf":
            ivf = col._index  # noqa: SLF001
            payload["collections"][name]["ivf"] = {
                "nlist": getattr(ivf, "nlist", 8),
                "nprobe": getattr(ivf, "nprobe", 2),
            }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def load_db(path: str | Path) -> VectorDB:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    db = VectorDB()
    for name, conf in data.get("collections", {}).items():
        ivf = conf.get("ivf") or {}
        col = db.create_collection(
            name,
            index_type=conf.get("index_type", "flat"),
            dimensions=conf.get("dimensions"),
            model_id=conf.get("model_id", "external"),
            nlist=ivf.get("nlist", 8),
            nprobe=ivf.get("nprobe", 2),
        )
        for row in conf.get("records", []):
            col._index.upsert(  # noqa: SLF001
                VectorRecord(
                    id=row["id"],
                    vector=tuple(row["vector"]),
                    metadata=row.get("metadata") or {},
                    text=row.get("text") or "",
                )
            )
        if conf.get("dimensions"):
            col._dimensions = conf["dimensions"]  # noqa: SLF001
        col.model_id = conf.get("model_id", col.model_id)
        if col.index_type == "ivf":
            col.rebuild()
    return db


def save_collection(col: Collection, path: str | Path) -> None:
    db = VectorDB()
    db._collections[col.name] = col  # noqa: SLF001
    save_db(db, path)
