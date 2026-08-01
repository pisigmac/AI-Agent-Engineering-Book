import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from authkit import AuthService
def test_rbac():
    a=AuthService(); k=a.issue_api_key("u", {"support"}); p=a.authenticate(k)
    assert a.authorize(p, "chat") and not a.authorize(p, "admin_only")
