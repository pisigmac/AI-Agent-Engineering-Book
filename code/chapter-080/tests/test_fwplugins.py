import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwplugins import Plugin, PluginManager
def test_allowlist():
    pm=PluginManager()
    with pytest.raises(PermissionError):
        pm.register(Plugin("x","ep", lambda: 1))
    pm.allow("x"); pm.register(Plugin("x","ep", lambda: 1)); assert pm.invoke("ep")[0]["result"]==1
