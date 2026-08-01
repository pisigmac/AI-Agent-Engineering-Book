"""Enterprise search: multi-query hybrid + parent expand + compress + rerank."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from advrag.compress import compress_hits
from advrag.corpus import build_parent_child_index
from advrag.hybrid import HybridRetriever
from advrag.parent_child import ParentChildIndex
from advrag.query_ops import expand_query, multi_queries
from advrag.rerank import SimpleReranker
from advrag.types import SearchHit, SearchResponse


@dataclass
class EnterpriseSearchConfig:
    mode: str = "hybrid"  # hybrid | bm25 | dense
    multi_query: bool = True
    n_queries: int = 3
    use_expansion: bool = True
    parent_expand: bool = True
    compress: bool = True
    rerank: bool = True
    candidate_k: int = 15
    final_k: int = 5
    compress_chars: int = 260


@dataclass
class EnterpriseSearch:
    """Composable advanced RAG retrieval for enterprise search demos."""

    retriever: HybridRetriever = field(default_factory=HybridRetriever)
    parents: ParentChildIndex = field(default_factory=ParentChildIndex)
    reranker: SimpleReranker = field(default_factory=SimpleReranker)
    config: EnterpriseSearchConfig = field(default_factory=EnterpriseSearchConfig)

    @classmethod
    def with_default_corpus(cls, **kwargs: Any) -> EnterpriseSearch:
        pci = build_parent_child_index()
        ret = HybridRetriever(candidate_k=20)
        ret.index(pci.all_indexable())
        return cls(retriever=ret, parents=pci, **kwargs)

    def search(self, query: str, *, filters: dict[str, Any] | None = None) -> SearchResponse:
        cfg = self.config
        if cfg.multi_query:
            queries = multi_queries(query, n=cfg.n_queries)
        elif cfg.use_expansion:
            queries = expand_query(query)
        else:
            queries = [query]

        # retrieve per reformulation
        lists: list[list[SearchHit]] = []
        for q in queries:
            hits = self.retriever.search(q, k=cfg.candidate_k, mode=cfg.mode)
            if filters:
                hits = [
                    h
                    for h in hits
                    if all(h.metadata.get(k) == v for k, v in filters.items())
                ]
            lists.append(hits)

        # fuse multi-query lists via RRF (also works for single list)
        from advrag.fusion import reciprocal_rank_fusion

        fused = reciprocal_rank_fusion(lists, k=cfg.candidate_k)

        if cfg.parent_expand:
            fused = self.parents.expand_to_parents(fused, k=cfg.candidate_k)

        if cfg.compress:
            # compress against original user query
            fused = compress_hits(query, fused, max_chars=cfg.compress_chars)

        if cfg.rerank:
            fused = self.reranker.rerank(query, fused, k=cfg.final_k)
        else:
            fused = fused[: cfg.final_k]
            fused = [
                SearchHit(
                    id=h.id,
                    text=h.text,
                    score=h.score,
                    metadata=h.metadata,
                    parent_id=h.parent_id,
                    sources=h.sources,
                    rank=i,
                )
                for i, h in enumerate(fused, start=1)
            ]

        return SearchResponse(
            query=query,
            hits=fused,
            expanded_queries=queries,
            strategy="enterprise",
            diagnostics={
                "mode": cfg.mode,
                "n_query_variants": len(queries),
                "parent_expand": cfg.parent_expand,
                "compress": cfg.compress,
                "rerank": cfg.rerank,
                "candidate_k": cfg.candidate_k,
                "final_k": cfg.final_k,
                "filters": filters or {},
            },
        )
