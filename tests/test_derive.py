"""Phase-5 tests. No network: stats fabricated, images generated."""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.derive import (crown, describe_image, dhash, file_proposed,
                          hamming, name_score, score)  # noqa: E402

# --- scoring orders by traction ---
a = {"mint": "A", "liq": 90000, "vol_h24": 400000, "txns_h24": 9000,
     "age_min": 300}
b = {"mint": "B", "liq": 2000, "vol_h24": 3000, "txns_h24": 120, "age_min": 20}
assert score(a) > score(b)
print("score: orders by traction")

# --- name match ---
assert name_score("MERRYMEN", ["merrymen", "milla"]) > 0.4
assert name_score("ZZQ9random", ["merrymen"]) == 0.0
assert name_score("", ["x"]) == 0.0
print("name_score: 3/3 pass")

# --- dhash: identical = 0, gradient vs inverse = far ---
from PIL import Image


def grad(inv=False):
    img = Image.new("L", (9, 8))
    img.putdata([255 - x * 28 if inv else x * 28 for y in range(8)
                 for x in range(9)])
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


h1, h2, h3 = dhash(grad()), dhash(grad()), dhash(grad(inv=True))
assert hamming(h1, h2) == 0, (h1, h2)
assert hamming(h1, h3) > 32, hamming(h1, h3)
print("dhash: identical 0, inverse far")

# --- vision unwired: never guesses ---
assert describe_image(grad()) is None
print("describe_image: None until a model is wired")

# --- crown: clear leader wins ---
r = crown([a, b])
assert r["leader"]["mint"] == "A" and r["reason"] == "ok", r

# --- crown: thin traction refuses ---
thin1 = {"mint": "T1", "liq": 100, "vol_h24": 200, "txns_h24": 5,
         "age_min": 5}
thin2 = {"mint": "T2", "liq": 150, "vol_h24": 250, "txns_h24": 8,
         "age_min": 6}
r = crown([thin1, thin2])
assert r["leader"] is None and "traction" in r["reason"], r
assert len(r["contenders"]) == 2

# --- crown: no margin refuses ---
c1 = {"mint": "C1", "liq": 60000, "vol_h24": 200000, "txns_h24": 4000,
      "age_min": 200}
c2 = {"mint": "C2", "liq": 62000, "vol_h24": 205000, "txns_h24": 4100,
      "age_min": 210}
r = crown([c1, c2])
assert r["leader"] is None and "margin" in r["reason"], r

# --- crown: crowd confirms the numbers-leader, holds against it ---
r = crown([c1, c2], crowd_pick="C2")
assert r["leader"] is not None and r["leader"]["mint"] == "C2" \
    and r["reason"] == "crowd-confirmed", r
r = crown([c1, c2], crowd_pick="C1")
assert r["leader"] is None and "crowd" in r["reason"], r

# --- crown: name + image bonuses lift the right one ---
d1 = {"mint": "D1", "symbol": "ZZZ", "liq": 60000, "vol_h24": 200000,
      "txns_h24": 4000, "age_min": 200}
d2 = {"mint": "D2", "symbol": "MERRYMEN", "liq": 62000, "vol_h24": 205000,
      "txns_h24": 4100, "age_min": 210}
r = crown([d1, d2], keywords=["merrymen"], image_dist={"D2": 2})
assert r["leader"] is None, r  # still no margin — bonuses don't fake it
print("crown: 6/6 pass (leader, thin-refuse, margin-refuse, crowd, honest)")

# --- intake: proposed goes to queue, dupes ignored, never a call ---
rows = []


class FakeCur:
    def __init__(self):
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        if q.strip().startswith("SELECT"):
            self._row = ("x",) if any(u == p[0] for u, _ in rows) else None
        else:
            rows.append((p[0], p[1]))
            self._row = (len(rows),)

    def fetchone(self):
        return self._row


class FakeConn:
    def cursor(self):
        return FakeCur()

    def commit(self):
        pass


conn = FakeConn()
assert file_proposed(conn, "0xabc", "robinhood") == 1
assert rows[0][1].startswith("derive:0xabc") and "pending" not in rows[0][1]
assert file_proposed(conn, "0xabc", "robinhood") is None  # dupe
assert len(rows) == 1
print("intake: proposed queued once, never a call row")
print("derive phase-5: all pass")
