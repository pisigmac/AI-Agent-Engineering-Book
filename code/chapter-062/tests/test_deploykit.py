import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploykit import EnvConfig, Rollout
def test_validate_and_plan():
    c=EnvConfig("prod","img:1", env={"DATABASE_URL":"x"}); assert c.validate()==[]
    p=Rollout("blue_green").plan("a","b"); assert p[0]["action"]=="deploy_green"
