import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scalekit import demo_scale, shard_goals
def test_scale():
    r=demo_scale([f"g{i}" for i in range(5)]); assert r["n_ok"]==5
def test_shard():
    s=shard_goals(["a","b","c","d"], shards=2); assert len(s)==2 and sum(len(x) for x in s)==4
