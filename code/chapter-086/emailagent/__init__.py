"""Email Agent — classify, prioritize, draft replies (no real SMTP)."""
from .agent import Email, EmailAgent, MockLLM, MockMailbox

__all__ = ["Email", "EmailAgent", "MockLLM", "MockMailbox"]
__version__ = "1.0.0"
