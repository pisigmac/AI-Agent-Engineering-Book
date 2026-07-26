"""Embeddings + offline semantic search for the evolving AI platform."""

from embedkit.index import DimensionMismatchError, InMemoryVectorIndex, ModelMismatchError
from embedkit.metrics import cosine_similarity, dot, euclidean_distance, l2_normalize
from embedkit.models import BagOfWordsEmbedder, HashingEmbedder, TfidfEmbedder
from embedkit.pipeline import EmbeddingPipeline
from embedkit.search import SearchResult, SemanticSearch, build_default_search
from embedkit.types import Document, SearchHit, VectorRecord

__all__ = [
    "BagOfWordsEmbedder",
    "DimensionMismatchError",
    "Document",
    "EmbeddingPipeline",
    "HashingEmbedder",
    "InMemoryVectorIndex",
    "ModelMismatchError",
    "SearchHit",
    "SearchResult",
    "SemanticSearch",
    "TfidfEmbedder",
    "VectorRecord",
    "build_default_search",
    "cosine_similarity",
    "dot",
    "euclidean_distance",
    "l2_normalize",
]

__version__ = "1.0.0"
