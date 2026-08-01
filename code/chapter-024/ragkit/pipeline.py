"""Production RAG pipeline: retrieve → rank → assemble → generate → memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ragkit.corpus import load_corpus
from ragkit.generator import Generator, GroundedExtractiveGenerator
from ragkit.memory import ConversationMemory
from ragkit.prompt import assemble_prompt
from ragkit.ranker import Ranker
from ragkit.retriever import InMemoryRetriever, Retriever
from ragkit.types import RAGAnswer


@dataclass
class RAGConfig:
    retrieve_k: int = 8
    final_k: int = 4
    min_retrieve_score: float | None = None
    include_prompt_in_result: bool = False


@dataclass
class RAGSystem:
    """End-to-end production-shaped RAG system (offline-capable)."""

    retriever: Retriever = field(default_factory=InMemoryRetriever)
    ranker: Ranker = field(default_factory=Ranker)
    generator: Generator = field(default_factory=GroundedExtractiveGenerator)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    config: RAGConfig = field(default_factory=RAGConfig)

    @classmethod
    def with_default_corpus(cls, **kwargs: Any) -> RAGSystem:
        system = cls(**kwargs)
        system.retriever.index(load_corpus())
        return system

    def ask(
        self,
        question: str,
        *,
        where: dict[str, Any] | None = None,
        use_memory: bool = True,
    ) -> RAGAnswer:
        if use_memory:
            self.memory.add_user(question)

        raw = self.retriever.retrieve(
            question,
            k=self.config.retrieve_k,
            where=where,
            min_score=self.config.min_retrieve_score,
        )
        ranked = self.ranker.rank(question, raw)[: self.config.final_k]
        mem_text = self.memory.render() if use_memory else ""
        # Exclude the just-added user turn from "prior" memory for prompt clarity:
        # render full memory is ok for multi-turn; for first turn it's only current user.
        prompt = assemble_prompt(
            question,
            ranked,
            memory_text=mem_text,
            max_evidence=self.config.final_k,
        )
        answer_text, grounded = self.generator.generate(prompt)

        if use_memory:
            self.memory.add_assistant(answer_text)

        return RAGAnswer(
            answer=answer_text,
            citations=prompt.citations,
            grounded=grounded,
            retrieved=ranked,
            prompt=prompt if self.config.include_prompt_in_result else None,
            memory_turns=len(self.memory),
            model_id=self.generator.model_id,
            diagnostics={
                "retrieve_k": self.config.retrieve_k,
                "final_k": self.config.final_k,
                "n_raw": len(raw),
                "n_ranked": len(ranked),
                "filters": where or {},
                "token_estimate": prompt.token_estimate,
                "retriever_model": getattr(
                    getattr(self.retriever, "embedder", None), "model_id", "unknown"
                ),
            },
        )

    def reset_memory(self) -> None:
        self.memory.clear()
