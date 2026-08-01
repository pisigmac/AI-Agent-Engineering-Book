"""PDF Chat — chunk, index, retrieve, answer with citations."""
from .rag import Chunk, InMemoryIndex, PdfChat, MockLLM, simple_chunk

__all__ = ["Chunk", "InMemoryIndex", "PdfChat", "MockLLM", "simple_chunk"]
__version__ = "1.0.0"
