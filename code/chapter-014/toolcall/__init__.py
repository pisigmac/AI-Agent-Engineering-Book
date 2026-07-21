"""Tool/function calling runtime for the bootcamp platform."""

from toolcall.loop import ToolLoop, weather_assistant
from toolcall.registry import ToolRegistry

__all__ = ["ToolLoop", "ToolRegistry", "weather_assistant"]
__version__ = "1.0.0"
