"""SQL Agent — NL→SQL with schema, allowlist, and dry-run safety."""
from .agent import SQLAgent, MockDB, MockLLM, Schema, FORBIDDEN

__all__ = ["SQLAgent", "MockDB", "MockLLM", "Schema", "FORBIDDEN"]
__version__ = "1.0.0"
