"""Persist FAISS index binary + JSON sidecar store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss

from faisskit.embed import HashEmbedder
from faisskit.indexes import IndexKind, build_index
from faisskit.service import FaissIndexService
from faisskit.store import DocStore


def save_service(service: FaissIndexService, directory: str | Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(service.raw_index(), str(directory / "index.faiss"))
    meta = {
        "kind": service.stats().kind,
        "dimensions": service.dimensions,
        "params": service.stats().params,
        "model_id": service.embedder.model_id,
        "store": service.store.to_dict(),
    }
    (directory / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_service(directory: str | Path) -> FaissIndexService:
    directory = Path(directory)
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    dimensions = int(meta["dimensions"])
    kind = meta.get("kind", IndexKind.FLAT_IP.value)
    params = meta.get("params") or {}
    svc = FaissIndexService(
        kind=kind,
        dimensions=dimensions,
        embedder=HashEmbedder(dimensions),
        nlist=int(params.get("nlist", 16)),
        nprobe=int(params.get("nprobe", 4)),
        hnsw_m=int(params.get("M", 32)),
        ef_search=int(params.get("efSearch", 16)),
    )
    # replace index with loaded binary
    svc._index = faiss.read_index(str(directory / "index.faiss"))  # noqa: SLF001
    svc._params = params  # noqa: SLF001
    svc._kind = IndexKind(kind)  # noqa: SLF001
    svc.store = DocStore.from_dict(meta.get("store") or {})
    return svc
