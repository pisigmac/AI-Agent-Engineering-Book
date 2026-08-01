"""Coding Agent — propose edits, run tests in a workspace sandbox."""
from .agent import CodingAgent, Workspace, MockLLM, TestRunner

__all__ = ["CodingAgent", "Workspace", "MockLLM", "TestRunner"]
__version__ = "1.0.0"
