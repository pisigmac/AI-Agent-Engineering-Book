"""Embedding model catalog, offline proxies, and retrieval benchmarks."""

from embbench.benchmark import run_benchmark, tradeoff_matrix
from embbench.catalog import default_catalog
from embbench.recommend import recommend

__all__ = [
    "default_catalog",
    "recommend",
    "run_benchmark",
    "tradeoff_matrix",
]

__version__ = "1.0.0"
