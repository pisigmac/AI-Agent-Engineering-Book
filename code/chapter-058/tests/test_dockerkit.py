import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dockerkit import write_assets, validate_assets
def test_generate():
    d=tempfile.mkdtemp(); r=write_assets(d); assert r["ok"] and r["checks"]["compose_exists"]
