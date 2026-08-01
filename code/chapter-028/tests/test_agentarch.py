import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentarch import AgentSkeleton, Skill

def test_skeleton_weather():
    r = AgentSkeleton().run("weather please")
    assert r["ok"] and "use_tools" in r["plan"]

def test_skill_registration():
    ag = AgentSkeleton()
    ag.register_skill(Skill("understand_goal", "x", lambda s: "skill-understood"))
    r = ag.run("anything")
    assert any(t["name"]=="understand_goal" for t in r["trace"])
