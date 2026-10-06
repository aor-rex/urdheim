"""GetXAPI read-path test: no key, no server, no postgres.
Covers: extract_tweet shapes, HMAC verify, handle_delivery gating
(real call queued w/ live DexScreener snapshot, chatter dropped),
getxapi client URL/auth/payload formation (stubbed httpx).
Usage: .venv/bin/python tests/getxapi_test.py
"""
import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["GETXAPI_WEBHOOK_SECRET"] = "testsecret"

from receiver.hook import extract_tweet, handle_delivery, verify  # noqa: E402

SUNUSI = "2vvw3cSwibzGD6SgW9QzRaBdmjkYrvs218DUy6VWpump"

# 1. payload shapes
a, i, t = extract_tweet({"tweet": {"id": "1", "text": "hi",
                                    "author": {"userName": "alice"}}})
assert (a, i, t) == ("alice", "1", "hi"), (a, i, t)
a, i, t = extract_tweet({"data": {"id_str": "2", "full_text": "yo",
                                  "screen_name": "bob"}})
assert (a, i, t) == ("bob", "2", "yo"), (a, i, t)
print("extract_tweet: nested tweet/data shapes OK")

# 2. HMAC
raw = b'{"hello":"world"}'
good = "sha256=" + hmac.new(b"testsecret", raw, hashlib.sha256).hexdigest()
assert verify(raw, good) and not verify(raw, "sha256=dead"), "hmac broken"
os.environ["GETXAPI_WEBHOOK_SECRET"] = ""
assert not verify(raw, good), "empty secret must fail closed"
os.environ["GETXAPI_WEBHOOK_SECRET"] = "testsecret"
print("verify: good/bad/empty-secret all correct")

# 3. delivery gating (live DexScreener snapshot)
qp = "/tmp/urdheim-gx-queue.jsonl"
if os.path.exists(qp):
    os.remove(qp)
n = handle_delivery({"tweet": {"id": "7001", "text": f"buying {SUNUSI} here gem",
                               "author": {"userName": "gxcaller"}}}, qp)
assert n == 1, n
n = handle_delivery({"tweet": {"id": "7002", "text": "great weather today",
                               "author": {"userName": "gxcaller"}}}, qp)
assert n == 0, n
rows = [json.loads(l) for l in open(qp)]
assert len(rows) == 1 and rows[0]["post_id"] == "7001", rows
assert (rows[0].get("snapshot") or {}).get("price"), "snapshot missing"
print(f"handle_delivery: call queued (price={rows[0]['snapshot']['price']}), "
      "chatter dropped")

# 4. client formation (stubbed transport)
import httpx  # noqa: E402
from watcher import getxapi as gx  # noqa: E402

os.environ["GETXAPI_KEY"] = "dummy"
seen = {}


def fake_request(method, url, **kw):
    seen["method"] = method
    seen["url"] = url
    seen["headers"] = kw.get("headers")
    seen["payload"] = kw.get("json") or kw.get("params")

    class R:
        def raise_for_status(self): pass

        def json(self):
            if "user/tweets" in url:
                return {"tweets": [{"id": "5", "text": "t"}],
                        "next_cursor": "CURSOR1"}
            return {"ok": True}
    return R()


gx.httpx.post = lambda url, **kw: fake_request("POST", url, **kw)
gx.httpx.get = lambda url, **kw: fake_request("GET", url, **kw)

gx.add_monitor("SomeCaller", "https://example.com/hook")
assert seen["url"] == "https://api.getxapi.com/twitter/monitor/add", seen
assert seen["headers"] == {"Authorization": "Bearer dummy"}, seen
assert seen["payload"]["userName"] == "SomeCaller", seen
assert seen["payload"]["tier"] == "fast", seen
print("add_monitor: URL/auth/handle-strip/tier OK")

tweets, cur = gx.backfill("SomeCaller")
assert tweets == [{"id": "5", "text": "t"}] and cur == "CURSOR1", (tweets, cur)
assert seen["payload"] == {"userName": "SomeCaller"}, seen
print("backfill: tweets + cursor OK")
print("GETXAPI READ PATH PASS")
