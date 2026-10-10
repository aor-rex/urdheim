"""Phase-3 tests. No DB, no network."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import listener.weekly as wk  # noqa: E402

ROWS = [("ryu_ngmi", 2, 4.5), ("ryunosoke", 1, 0.0), ("vet", 1, 9.2)]


class FakeCur:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        pass

    def fetchall(self):
        return ROWS


class FakeConn:
    def cursor(self):
        return FakeCur()


sent = []
wk.post = lambda text, dry=True, allow_live=False: (
    sent.append(text) or {"live": True} if (not dry and allow_live)
    else {"dry": True})

conn = FakeConn()
assert [r["handle"] for r in wk.top_week(conn)] == \
    ["ryu_ngmi", "ryunosoke", "vet"]

text = wk.fmt_week(wk.top_week(conn))
assert text.startswith("top callers this week"), text
assert "1. @ryu_ngmi — 2 calls · 4.5x best" in text, text
assert "2. @ryunosoke — 1 call" in text, text  # singular, no best
assert text.endswith("/leaderboard"), text
assert len(text) <= 280, len(text)

# dry posts nothing
out = wk.run(conn, live=False)
assert out["dry"] and sent == [], (out, sent)

# live posts once
out = wk.run(conn, live=True, allow=True)
assert out["posted"] and len(sent) == 1, (out, sent)

# empty week posts nothing
wk.top_week = lambda conn, limit=3: []
out = wk.run(conn, live=True, allow=True)
assert out["posted"] is False and len(sent) == 1, out

print("weekly: 8/8 pass")
