import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coding import CodingAgent, Workspace, MockLLM


def test_add_function_passes():
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("add function add")
    assert out["ok"] is True
    assert "mathutil.py" in out["files"]


def test_multiply():
    agent = CodingAgent(workspace=Workspace(), llm=MockLLM())
    out = agent.run("fix multiply")
    assert out["ok"] is True
