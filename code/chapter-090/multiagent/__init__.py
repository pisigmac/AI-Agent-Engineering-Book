"""Multi-Agent Platform — router, specialists, shared bus, final merge."""
from .platform import AgentSpec, MessageBus, Router, MultiAgentPlatform, MockLLM

__all__ = ["AgentSpec", "MessageBus", "Router", "MultiAgentPlatform", "MockLLM"]
__version__ = "1.0.0"
