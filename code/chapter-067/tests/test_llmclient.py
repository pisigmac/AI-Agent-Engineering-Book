import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llmclient import LLMClient, MockProvider
def test_complete_retry():
    c=LLMClient(MockProvider(fail_times=2), max_retries=3, backoff_s=0)
    r=c.complete([{"role":"user","content":"hi"}]); assert r["attempts"]==3 and "hi" in r["text"]
def test_stream():
    chunks=LLMClient(MockProvider()).stream([{"role":"user","content":"abcdef"}]); assert "".join(chunks)
