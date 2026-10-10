"""Phase-1 outbox tests. No network: unyx is stubbed, dry runs never touch it."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# stub unyx before outbox imports it
calls = []
unyx = types.ModuleType("unyx")


class FakeClient:
    def __enter__(self):
        calls.append("login")
        return self

    def __exit__(self, *a):
        return False

    def login_from_cookies(self, path):
        assert path == "/tmp/fake-cookies.json"
        return True

    def reply(self, pid, text):
        calls.append(("reply", pid, text))
        return {"id": "r1"}

    def post(self, text):
        calls.append(("post", text))
        return {"id": "p1"}


unyx.UnyxClient = FakeClient
sys.modules["unyx"] = unyx

os.environ["LISTENER_COOKIES"] = "/tmp/fake-cookies.json"
import listener.outbox as ob  # noqa: E402

# 1. dry reply never touches the client
r = ob.reply("123", "hello")
assert r["dry"] and not r["live"] and calls == [], r

# 2. no-allow flag blocks live even with dry=False
r = ob.reply("123", "hello", dry=False)
assert not r["live"] and r["reason"] == "no-allow" and calls == [], r

# 3. live reply goes through
r = ob.reply("123", "hello", dry=False, allow_live=True)
assert r["live"] and calls == ["login", ("reply", "123", "hello")], (r, calls)

# 4. quote appends tweet url
calls.clear()
r = ob.quote("999", "called it", dry=False, allow_live=True)
assert r["verb"] == "quote" and calls[-1][0] == "post" \
    and "x.com/i/status/999" in calls[-1][1], (r, calls)

# 5. over-280 refused before any send
calls.clear()
try:
    ob.post("x" * 281, dry=False, allow_live=True)
    raise SystemExit("FAIL: oversize posted")
except ValueError:
    pass
assert calls == []

# 6. day cap refuses
ob.DAY_CAP = 0
try:
    ob.post("hi", dry=False, allow_live=True)
    raise SystemExit("FAIL: cap ignored")
except RuntimeError as e:
    assert "day cap" in str(e), e

print("outbox phase-1: 6/6 pass")
