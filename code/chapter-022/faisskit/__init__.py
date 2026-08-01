"""FAISS-backed indexing and PDF search for the AI platform."""

from faisskit.pdf_search import PdfSearchEngine, build_sample_pdfs
from faisskit.service import FaissIndexService
from faisskit.types import IndexKind, SearchResult

__all__ = [
    "FaissIndexService",
    "IndexKind",
    "PdfSearchEngine",
    "SearchResult",
    "build_sample_pdfs",
]

__version__ = "1.0.0"
