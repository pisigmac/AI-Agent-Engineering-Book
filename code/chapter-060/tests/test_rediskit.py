import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rediskit import RedisLite
def test_cache_and_rate():
    r=RedisLite(); r.set("a",1); assert r.get("a")==1
    assert r.allow_rate("u", limit=2, window_s=60)
    assert r.allow_rate("u", limit=2, window_s=60)
    assert not r.allow_rate("u", limit=2, window_s=60)
