import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multiagent import AgentSpec, MultiAgentPlatform, MockLLM, Router


def _agents():
    return [
        AgentSpec("researcher", ["research", "search"], lambda t, _: f"notes on {t}"),
        AgentSpec("coder", ["code", "implement", "fix"], lambda t, _: f"patch for {t}"),
        AgentSpec("writer", ["write", "summary"], lambda t, _: f"draft for {t}"),
    ]


def test_route_coder():
    r = Router(_agents())
    assert r.route("implement feature") .name == "coder"


def test_single_and_fanout():
    plat = MultiAgentPlatform(agents=_agents(), llm=MockLLM())
    out = plat.run("write a summary")
    assert out["agents"] == ["writer"]
    out2 = MultiAgentPlatform(agents=_agents(), llm=MockLLM()).run("research code", fanout=True)
    assert len(out2["agents"]) == 3
    assert "Merged" in out2["result"]
