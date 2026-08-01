"""Post-retrieval ranking: metadata boosts + lexical overlap blend."""

from __future__ import annotations

from ragkit.embed import tokenize
from ragkit.types import RetrievedChunk


class Ranker:
    """Re-rank retrieved chunks before prompt assembly."""

    def __init__(
        self,
        *,
        lexical_weight: float = 0.25,
        topic_boosts: dict[str, float] | None = None,
    ) -> None:
        if not 0.0 <= lexical_weight <= 1.0:
            raise ValueError("lexical_weight in [0,1]")
        self.lexical_weight = lexical_weight
        self.topic_boosts = topic_boosts or {}

    def rank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []
        q_toks = set(tokenize(query))
        rescored: list[RetrievedChunk] = []
        for ch in chunks:
            d_toks = set(tokenize(ch.text))
            overlap = len(q_toks & d_toks) / max(len(q_toks), 1)
            dense = ch.score
            blended = (1.0 - self.lexical_weight) * dense + self.lexical_weight * overlap
            topic = str(ch.metadata.get("topic", ""))
            boost = self.topic_boosts.get(topic, 1.0)
            final = blended * boost
            rescored.append(
                RetrievedChunk(
                    id=ch.id,
                    text=ch.text,
                    score=ch.score,
                    metadata=dict(ch.metadata),
                    rank=ch.rank,
                    ranker_score=final,
                )
            )
        rescored.sort(key=lambda c: (-(c.ranker_score or 0.0), c.id))
        return [
            RetrievedChunk(
                id=c.id,
                text=c.text,
                score=c.score,
                metadata=c.metadata,
                rank=i,
                ranker_score=c.ranker_score,
            )
            for i, c in enumerate(rescored, start=1)
        ]
