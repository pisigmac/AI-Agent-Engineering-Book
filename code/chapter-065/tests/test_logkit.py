import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logkit import Logger
def test_correlation():
    log=Logger("svc"); log.info("a"); log.error("b", x=1)
    assert log.records[0]["correlation_id"]==log.records[1]["correlation_id"]
    assert "correlation_id" in log.dump()
