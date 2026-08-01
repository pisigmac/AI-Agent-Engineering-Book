import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from promptmgr import default_manager
def test_version_and_render():
    m=default_manager(); assert "Acme" in m.render("support", product="Acme", issue="x")
    assert "User: x" in m.render("support", version="1.0.0", issue="x")
def test_missing_var():
    m=default_manager()
    with pytest.raises(KeyError):
        m.render("support", version="1.1.0", issue="x")
