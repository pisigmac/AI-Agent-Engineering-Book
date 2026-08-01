"""Compare flat vs IVF on the same data: scan count, latency, top-1 agreement."""

from __future__ import annotations

import time
from typing import Any

from vectordb.database import VectorDB
from vectordb.embed import HashEmbedder


def compare_indexes(
    documents: list[dict[str, Any]],
    queries: list[str],
    *,
    k: int = 3,
    nlist: int = 4,
    nprobe: int = 2,
) -> dict[str, Any]:
    emb = HashEmbedder(64)
    db = VectorDB()
    flat = db.create_collection("flat", index_type="flat", dimensions=64)
    ivf = db.create_collection("ivf", index_type="ivf", dimensions=64, nlist=nlist, nprobe=nprobe)

    for doc in documents:
        vec = emb.embed([doc["text"]])[0]
        meta = doc.get("metadata") or {}
        flat.upsert(id=doc["id"], vector=vec, text=doc["text"], metadata=meta)
        ivf.upsert(id=doc["id"], vector=vec, text=doc["text"], metadata=meta)
    ivf.rebuild()

    rows = []
    agree = 0
    for q in queries:
        qv = emb.embed([q])[0]
        t0 = time.perf_counter()
        rf = flat.query(vector=qv, k=k)
        tf = (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        ri = ivf.query(vector=qv, k=k)
        ti = (time.perf_counter() - t1) * 1000
        top_f = rf.hits[0].id if rf.hits else None
        top_i = ri.hits[0].id if ri.hits else None
        if top_f == top_i:
            agree += 1
        rows.append(
            {
                "query": q,
                "flat_top": top_f,
                "ivf_top": top_i,
                "flat_scanned": rf.n_scanned,
                "ivf_scanned": ri.n_scanned,
                "flat_ms": round(tf, 4),
                "ivf_ms": round(ti, 4),
            }
        )
    n = max(len(queries), 1)
    return {
        "n_docs": len(documents),
        "n_queries": len(queries),
        "top1_agreement": round(agree / n, 4),
        "avg_flat_scanned": round(sum(r["flat_scanned"] for r in rows) / n, 2),
        "avg_ivf_scanned": round(sum(r["ivf_scanned"] for r in rows) / n, 2),
        "details": rows,
    }
