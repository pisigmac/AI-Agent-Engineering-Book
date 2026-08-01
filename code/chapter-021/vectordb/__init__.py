"""Mini vector database: collections, indexes, filters, persistence."""

from vectordb.database import VectorDB
from vectordb.types import QueryHit, QueryResult, VectorRecord

__all__ = [
    "QueryHit",
    "QueryResult",
    "VectorDB",
    "VectorRecord",
]

__version__ = "1.0.0"
