"""Meme-watch tests. No network: pools/vision stubbed, conn faked."""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain import watch as W  # noqa: E402
import brain.derive as derive_mod  # noqa: E402
import brain.hints as hints_mod  # noqa: E402


def grad(seed=0):
    from PIL import Image
    img = Image.new("L", (16, 16))
    img.putdata([(x * 7 + y * 13 + seed) % 256
                 for y in range(16) for x in range(16)])
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class FakeCur:
    def __init__(self, conn):
        self.c = conn
        self._row = None
        self._rows = []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        p = p or ()
        if "FROM meme_watches WHERE image_hash" in q:
            h = p[0]
            self._row = (("watching",) if h in self.c.watches else None)
        elif "COUNT(*) FROM meme_watches" in q:
            self._row = (sum(1 for w in self.c.watches.values()
                             if w["status"] == "watching"),)
        elif "INSERT INTO meme_watches" in q:
            self.c.watches[p[0]] = {"keywords": p[1], "status": "watching"}
            self._row = None
        elif "SET status='expired'" in q:
            self.rowcount = 0
            self._row = None
        elif "FROM meme_watches WHERE status='watching'" in q:
            self._rows = [(i, w["keywords"], "p1", "ryu")
                          for i, w in self.c.watches.items()
                          if w["status"] == "watching"][:20]
        elif "SET status='filed'" in q:
            self._row = None
        elif "FROM callers" in q:
            self._row = None
        elif "INSERT INTO callers" in q:
            self._row = (1,)
        elif "INSERT INTO calls" in q:
            self.c.calls.append(p)
            self._row = None
        else:
            self._row = None

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeConn:
    def __init__(self):
        self.watches = {}
        self.calls = {}

    def cursor(self):
        if isinstance(self.calls, dict):
            self.calls = []
        return FakeCur(self)

    def commit(self):
        pass


# stub vision: frog meme
_real_desc = derive_mod.describe_image
derive_mod.describe_image = lambda png: "a green frog holding a coin"
# stub pools: nothing at first
hints_mod_search = hints_mod.search_pools
hints_mod.search_pools = lambda kw: []

c = FakeConn()
r = W.handle_meme(c, grad(), "p1", "ryu", ["FROG"])
assert r and "radar" in r and "@ryu" in r, r
assert len(c.watches) == 1, c.watches
print("open: watch + radar reply")

# dupe image -> silence
r2 = W.handle_meme(c, grad(), "p2", "ryu", ["FROG"])
assert r2 is None, r2
print("dupe: silence")

# pool appears -> recheck files hinted
solo = [{"mint": "0xfrog", "chain": "robinhood", "symbol": "FROG",
         "liq": 90000, "vol_h24": 400000, "txns_h24": 8000, "age_min": 300}]
hints_mod.search_pools = lambda kw: solo if kw.upper() == "FROG" else []
out = W.recheck(c, dry=True, allow_live=False)
assert out["filed"] == 1, out
assert c.calls and c.calls[0][1] == "FROG", c.calls
print("recheck: filed hinted once pool clears")

# pool never comes -> nothing filed, watch stays
hints_mod.search_pools = lambda kw: []
c2 = FakeConn()
W.handle_meme(c2, grad(seed=5), "p9", "ryu", ["ZOOM"])
out2 = W.recheck(c2, dry=True, allow_live=False)
assert out2["filed"] == 0 and out2["watched"] == 1, out2
assert c2.calls == [], c2.calls
print("recheck: thin stays watching, nothing filed")

derive_mod.describe_image = _real_desc
hints_mod.search_pools = hints_mod_search
print("watch: all pass")
