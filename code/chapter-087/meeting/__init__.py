"""Meeting Assistant — transcript → summary, decisions, action items."""
from .assistant import MeetingAssistant, Transcript, MockLLM, ActionItem

__all__ = ["MeetingAssistant", "Transcript", "MockLLM", "ActionItem"]
__version__ = "1.0.0"
