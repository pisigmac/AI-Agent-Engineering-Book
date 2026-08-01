"""Index optimization helpers: nprobe sweeps, kind comparison."""

from __future__ import annotations

import time
from typing import Any

from faisskit.service import FaissIndexService
from faisskit.types import IndexKind


def sweep_nprobe(
    service: FaissIndexService,
    queries: list[str],
    *,
    nprobes: list[int] | None = None,
    k: int = 3,
) -> list[dict[str, Any]]:
    """Measure latency vs nprobe for IVF indexes."""
    if service.stats().kind != IndexKind.IVF_FLAT.value:
        return [{"warning": "sweep_nprobe is for ivf_flat indexes", "kind": service.stats().kind}]
    nprobes = nprobes or [1, 2, 4, 8]
    rows = []
    for npb in nprobes:
        service.configure(nprobe=npb)
        t0 = time.perf_counter()
        tops = []
        for q in queries:
            r = service.search(q, k=k)
            tops.append(r.hits[0].id if r.hits else None)
        ms = (time.perf_counter() - t0) * 1000 / max(len(queries), 1)
        rows.append({"nprobe": npb, "avg_ms": round(ms, 4), "sample_tops": tops[:3]})
    return rows


def compare_kinds(
    docs: list[dict[str, Any]],
    queries: list[str],
    *,
    kinds: list[str] | None = None,
    dimensions: int = 64,
    k: int = 3,
) -> dict[str, Any]:
    kinds = kinds or [
        IndexKind.FLAT_IP.value,
        IndexKind.IVF_FLAT.value,
        IndexKind.HNSW.value,
    ]
    services: dict[str, FaissIndexService] = {}
    for kind in kinds:
        kwargs: dict[str, Any] = {"kind": kind, "dimensions": dimensions}
        if kind == IndexKind.IVF_FLAT.value:
            kwargs.update({"nlist": max(4, min(16, len(docs))), "nprobe": 2})
        svc = FaissIndexService(**kwargs)
        svc.add_documents(docs)
        services[kind] = svc

    # flat as reference for top-1 agreement
    ref = services.get(IndexKind.FLAT_IP.value) or next(iter(services.values()))
    rows = []
    for kind, svc in services.items():
        agree = 0
        t0 = time.perf_counter()
        for q in queries:
            r = svc.search(q, k=k)
            rr = ref.search(q, k=k)
            top = r.hits[0].id if r.hits else None
            rtop = rr.hits[0].id if rr.hits else None
            if top == rtop:
                agree += 1
        ms = (time.perf_counter() - t0) * 1000 / max(len(queries), 1)
        rows.append(
            {
                "kind": kind,
                "ntotal": svc.ntotal,
                "avg_ms": round(ms, 4),
                "top1_agreement_vs_flat": round(agree / max(len(queries), 1), 4),
                "stats": svc.stats().to_dict(),
            }
        )
    return {"results": rows, "reference": ref.stats().kind}
