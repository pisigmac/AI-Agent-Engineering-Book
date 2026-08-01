import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pgkit import AgentStore
def test_store():
    s=AgentStore(); s.upsert_agent("a","n"); s.create_run("r","a","g"); s.finish_run("r","succeeded","ok")
    assert s.get_run("r")["status"]=="succeeded"
