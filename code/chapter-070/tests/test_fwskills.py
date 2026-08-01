import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwskills import default_registry
def test_compose():
    assert default_registry().compose(["lower","exclaim"], "Hi")=="hi!"
