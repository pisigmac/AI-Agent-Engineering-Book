import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oaiagents.runtime import demo
def test_run():
    r = demo().run("support", "weather please")
    assert r["ok"] and r["framework"]=="openai_agents_sdk"
