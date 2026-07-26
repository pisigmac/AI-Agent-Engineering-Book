"""Chunking strategies for retrieval-ready passages."""

from chunkkit.pipeline import chunk_document, compare_strategies
from chunkkit.types import Chunk, ChunkReport, ChunkStrategy, SourceDocument

__all__ = [
    "Chunk",
    "ChunkReport",
    "ChunkStrategy",
    "SourceDocument",
    "chunk_document",
    "compare_strategies",
]

__version__ = "1.0.0"
