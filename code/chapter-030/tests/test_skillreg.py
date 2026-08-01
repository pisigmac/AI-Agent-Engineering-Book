import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skillreg import default_registry
def test_list_and_run():
    r=default_registry(); assert any(s["name"]=="normalize" for s in r.list())
    assert r.get("normalize").run(text="  Hi ")=="hi"
def test_compose_and_discover():
    r=default_registry()
    out=r.compose(["normalize","summarize"], "  Hello World  ")
    assert "SUMMARY" in out and "hello world" in out
    assert "summarize" in r.discover("nlp")
