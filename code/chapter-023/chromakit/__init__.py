"""Chroma-backed knowledge store and assistant for the AI platform."""

from chromakit.assistant import KnowledgeAssistant
from chromakit.store import ChromaStore
from chromakit.types import AssistantAnswer, QueryResult

__all__ = [
    "AssistantAnswer",
    "ChromaStore",
    "KnowledgeAssistant",
    "QueryResult",
]

__version__ = "1.0.0"
