import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modechoice import select_mode
def test_workflow():
    assert select_mode("nightly ETL batch").mode == "workflow"
def test_agent():
    assert select_mode("research why latency spiked").mode == "agent"
def test_hybrid():
    assert select_mode("lookup weather for ticket").mode == "hybrid"
