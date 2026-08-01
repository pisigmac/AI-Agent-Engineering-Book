from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentkit import AutonomousAgent, Goal

def test_weather_goal():
    r = AutonomousAgent().run("What is the weather in Paris?")
    assert r.ok and r.state.value == "succeeded"
    assert any("weather:" in str(s) for s in r.steps)

def test_refund_goal():
    r = AutonomousAgent().run("Explain the refund policy")
    assert r.ok
    assert any("policy:" in str(s) for s in r.steps)

def test_max_steps():
    # empty-ish goal still finishes via clarify path
    r = AutonomousAgent(max_steps=2).run("hello")
    assert r.steps
