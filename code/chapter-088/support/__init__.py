"""Customer Support Agent — KB retrieval, reply, escalate, ticket state."""
from .agent import SupportAgent, Ticket, KnowledgeBase, MockLLM

__all__ = ["SupportAgent", "Ticket", "KnowledgeBase", "MockLLM"]
__version__ = "1.0.0"
