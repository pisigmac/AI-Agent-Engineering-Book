"""FAISS index factory: Flat, IVF, HNSW + ID maps."""

from __future__ import annotations

from typing import Any

import faiss
import numpy as np

from faisskit.types import IndexKind


def build_index(
    kind: IndexKind | str,
    dimensions: int,
    *,
    nlist: int = 16,
    nprobe: int = 4,
    hnsw_m: int = 32,
    ef_construction: int = 40,
    ef_search: int = 16,
) -> tuple[faiss.Index, dict[str, Any]]:
    """Create a FAISS index wrapped with IndexIDMap2 for external int64 ids."""
    kind = IndexKind(kind)
    if dimensions < 1:
        raise ValueError("dimensions must be >= 1")

    params: dict[str, Any] = {"kind": kind.value, "dimensions": dimensions}

    if kind is IndexKind.FLAT_IP:
        base = faiss.IndexFlatIP(dimensions)
        metric = "ip"
    elif kind is IndexKind.FLAT_L2:
        base = faiss.IndexFlatL2(dimensions)
        metric = "l2"
    elif kind is IndexKind.IVF_FLAT:
        quantizer = faiss.IndexFlatIP(dimensions)
        nlist = max(1, nlist)
        base = faiss.IndexIVFFlat(quantizer, dimensions, nlist, faiss.METRIC_INNER_PRODUCT)
        base.nprobe = max(1, min(nprobe, nlist))
        params.update({"nlist": nlist, "nprobe": base.nprobe})
        metric = "ip"
    elif kind is IndexKind.HNSW:
        base = faiss.IndexHNSWFlat(dimensions, hnsw_m, faiss.METRIC_INNER_PRODUCT)
        base.hnsw.efConstruction = ef_construction
        base.hnsw.efSearch = ef_search
        params.update({"M": hnsw_m, "efConstruction": ef_construction, "efSearch": ef_search})
        metric = "ip"
    else:
        raise ValueError(f"unsupported kind: {kind}")

    params["metric"] = metric
    # IDMap2 lets us add with external ids and remove by id
    index = faiss.IndexIDMap2(base)
    return index, params


def train_if_needed(index: faiss.Index, vectors: np.ndarray) -> None:
    """Train IVF (and similar) when required."""
    base = _unwrap(index)
    if getattr(base, "is_trained", True):
        return
    if vectors.ndim != 2 or vectors.shape[0] == 0:
        raise ValueError("need vectors to train index")
    # IVF requires at least nlist training points ideally
    base.train(np.ascontiguousarray(vectors, dtype=np.float32))


def set_nprobe(index: faiss.Index, nprobe: int) -> None:
    base = _unwrap(index)
    if hasattr(base, "nprobe"):
        base.nprobe = max(1, int(nprobe))


def set_ef_search(index: faiss.Index, ef_search: int) -> None:
    base = _unwrap(index)
    if hasattr(base, "hnsw"):
        base.hnsw.efSearch = max(1, int(ef_search))


def _unwrap(index: faiss.Index) -> faiss.Index:
    if isinstance(index, faiss.IndexIDMap2) or isinstance(index, faiss.IndexIDMap):
        return faiss.downcast_index(index.index)
    return index


def index_kind_from_params(params: dict[str, Any]) -> str:
    return str(params.get("kind", "unknown"))
