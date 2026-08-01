"""Simple IVF-style index for teaching approximate search.

Assign each vector to a coarse centroid (random/sample k-means-lite).
Query probes the nearest ``nprobe`` lists only — fewer scans, possible recall loss.
"""

from __future__ import annotations

import random
from collections import defaultdict

from vectordb.metrics import dot, l2_normalize
from vectordb.types import QueryHit, VectorRecord


class IVFIndex:
    index_type = "ivf"

    def __init__(
        self,
        *,
        nlist: int = 8,
        nprobe: int = 2,
        seed: int = 7,
    ) -> None:
        if nlist < 1 or nprobe < 1:
            raise ValueError("nlist/nprobe must be >= 1")
        self.nlist = nlist
        self.nprobe = min(nprobe, nlist)
        self.seed = seed
        self._records: dict[str, VectorRecord] = {}
        self._lists: dict[int, set[str]] = defaultdict(set)
        self._centroids: list[list[float]] = []
        self.dimensions: int | None = None
        self._built = False

    def clear(self) -> None:
        self._records.clear()
        self._lists.clear()
        self._centroids = []
        self.dimensions = None
        self._built = False

    def __len__(self) -> int:
        return len(self._records)

    def upsert(self, record: VectorRecord) -> None:
        dim = len(record.vector)
        if self.dimensions is None:
            self.dimensions = dim
        elif dim != self.dimensions:
            raise ValueError(f"dim {dim} != index dim {self.dimensions}")
        # remove old assignment
        if record.id in self._records:
            self._unassign(record.id)
        self._records[record.id] = record
        self._built = False  # lazy rebuild on search

    def delete(self, doc_id: str) -> bool:
        if doc_id not in self._records:
            return False
        self._unassign(doc_id)
        del self._records[doc_id]
        return True

    def get(self, doc_id: str) -> VectorRecord | None:
        return self._records.get(doc_id)

    def records(self) -> list[VectorRecord]:
        return list(self._records.values())

    def _unassign(self, doc_id: str) -> None:
        for ids in self._lists.values():
            ids.discard(doc_id)

    def build(self) -> None:
        """(Re)build coarse centroids and inverted lists."""
        self._lists = defaultdict(set)
        self._centroids = []
        if not self._records:
            self._built = True
            return
        vecs = [list(r.vector) for r in self._records.values()]
        ids = [r.id for r in self._records.values()]
        nlist = min(self.nlist, len(vecs))
        rng = random.Random(self.seed)
        # init centroids from random samples
        picks = rng.sample(range(len(vecs)), nlist)
        self._centroids = [list(vecs[i]) for i in picks]
        # one-pass assignment + centroid mean update
        for _ in range(3):
            buckets: dict[int, list[list[float]]] = defaultdict(list)
            assign: dict[str, int] = {}
            for doc_id, v in zip(ids, vecs):
                cid = self._nearest_centroid(v)
                assign[doc_id] = cid
                buckets[cid].append(v)
            for cid, members in buckets.items():
                if not members:
                    continue
                dim = len(members[0])
                mean = [0.0] * dim
                for m in members:
                    for j, x in enumerate(m):
                        mean[j] += x
                mean = [x / len(members) for x in mean]
                self._centroids[cid] = l2_normalize(mean)
            # pad empty centroids
            while len(self._centroids) < nlist:
                self._centroids.append(list(vecs[rng.randrange(len(vecs))]))
        self._lists = defaultdict(set)
        for doc_id, v in zip(ids, vecs):
            cid = self._nearest_centroid(v)
            self._lists[cid].add(doc_id)
        self._built = True

    def _nearest_centroid(self, v: list[float] | tuple[float, ...]) -> int:
        best_i, best_s = 0, float("-inf")
        for i, c in enumerate(self._centroids):
            s = dot(v, c)
            if s > best_s:
                best_s, best_i = s, i
        return best_i

    def search(
        self,
        query: list[float] | tuple[float, ...],
        *,
        k: int = 10,
        min_score: float | None = None,
        allow_ids: set[str] | None = None,
    ) -> tuple[list[QueryHit], int]:
        if k < 1:
            raise ValueError("k >= 1")
        if not self._built:
            self.build()
        if not self._records:
            return [], 0
        if self.dimensions is not None and len(query) != self.dimensions:
            raise ValueError(f"query dim {len(query)} != {self.dimensions}")

        # probe nearest coarse lists
        cent_scores = [(i, float(dot(query, c))) for i, c in enumerate(self._centroids)]
        cent_scores.sort(key=lambda t: -t[1])
        probe = {i for i, _ in cent_scores[: self.nprobe]}

        candidate_ids: set[str] = set()
        for cid in probe:
            candidate_ids |= self._lists.get(cid, set())

        scored: list[tuple[float, VectorRecord]] = []
        scanned = 0
        for doc_id in candidate_ids:
            if allow_ids is not None and doc_id not in allow_ids:
                continue
            rec = self._records[doc_id]
            scanned += 1
            score = float(dot(query, rec.vector))
            if min_score is not None and score < min_score:
                continue
            scored.append((score, rec))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        hits = [
            QueryHit(
                id=rec.id,
                score=score,
                metadata=dict(rec.metadata),
                text=rec.text,
                rank=i,
            )
            for i, (score, rec) in enumerate(scored[:k], start=1)
        ]
        return hits, scanned
