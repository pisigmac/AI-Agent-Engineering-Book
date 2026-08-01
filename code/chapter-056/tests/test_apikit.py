import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apikit import build_app, Request
def test_health_and_auth():
    app=build_app()
    assert app.handle(Request("/health")).status==200
    assert app.handle(Request("/v1/chat","POST",headers={"x-api-key":"dev-key"},json_body={"message":"x"})).status==200
    assert app.handle(Request("/v1/chat","POST",json_body={"message":"x"})).status==401
