import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwsched import Scheduler
def test_priority():
    s=Scheduler(); order=[]
    s.schedule("low", lambda: order.append("low"), priority=10)
    s.schedule("high", lambda: order.append("high"), priority=1)
    s.tick(0); assert order[0]=="high"
