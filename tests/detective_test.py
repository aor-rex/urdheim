"""Detective plumbing test: stubbed LLM + stubbed psycopg over the fixture queue.
Verifies verdict gating (>=0.7 + call/soft-shill) and record_call SQL.
Usage: .venv/bin/python tests/detective_test.py
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "brain"))

os.environ["DB_URL"] = "postgresql://test/test@localhost/test"
os.environ["QUEUE_PATH"] = "/tmp/urdheim-test-queue.jsonl"
os.environ["OPENCODE_API_KEY"] = "dummy"
os.environ["DETECT_MODEL"] = "dummy"

VERDICTS = {
    "9001": {"verdict": "call", "confidence": 0.92,
             "evidence": "apeing 2vvw3cSwibzGD6SgW9QzRaBdmjkYrvs218DUy6VWpump here"},
    "9003": {"verdict": "chatting", "confidence": 0.6, "evidence": "just observing"},
}

statements = []


class FakeCur:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, q, p=None): statements.append((q, p))
    def fetchone(self): return [7]


class FakeConn:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def cursor(self): return FakeCur()
    def commit(self): pass


m = types.ModuleType("psycopg")
m.connect = lambda *a, **k: FakeConn()
sys.modules["psycopg"] = m

import detective

detective.classify = lambda author, text: dict(
    VERDICTS["9001"] if "apeing" in text else VERDICTS["9003"])
detective.main()

inserts = [s for s in statements if "INSERT INTO calls" in s[0]]
callers = [s for s in statements if "INSERT INTO callers" in s[0]]
assert len(inserts) == 1, f"expected 1 calls insert, got {len(inserts)}"
assert len(callers) == 1, f"expected 1 caller insert, got {len(callers)}"
params = inserts[0][1]
assert params[0] == 7 and params[2].startswith("2vvw3cSw"), params
assert params[7] == "call" and params[8] == 0.92, params[7:9]
print("DETECTIVE PASS: 9001 recorded (call/0.92), 9003 gated out (chatting), "
      "caller upsert + calls insert well-formed")
