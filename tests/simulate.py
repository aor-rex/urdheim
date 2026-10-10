"""Full-story simulation: every new write-side flow, one script, no network.

Acts: ask -> confirm -> silence-expiry -> milestone quote -> weekly post
      -> derivation crown -> soft-shill hint. Run:
  .venv/bin/python tests/simulate.py
All sends dry. Chain/X/DB are fakes. Doubles as an e2e invariant check.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---- fake chain: price runs 4x across the story ----
PRICE = {"p": 0.001}
wc = types.ModuleType("watcher.common")
wc.detect_chain = lambda m: "robinhood" if m.startswith("0x") else "solana"
wc.snapshot_price = lambda m, c=None: {"price": PRICE["p"],
                                       "mcap": PRICE["p"] * 50_000_000,
                                       "symbol": "MEME", "liq": 9000.0}
wc.find_cas = lambda t: ["0xabc"] if "0xabc" in t else []
sys.modules["watcher"] = types.ModuleType("watcher")
sys.modules["watcher.common"] = wc

# ---- fake db ----
DB = {"asks": [], "callers": [{"id": 1, "handle": "ryu_ngmi"}],
      "calls": [], "subs": []}
AID = [0]


class Cur:
    def __init__(self):
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        n = " ".join(q.split())
        if "INSERT INTO asks" in n:
            if any(r["ask_post_id"] == p[3] for r in DB["asks"]):
                self.rows = []
            else:
                AID[0] += 1
                DB["asks"].append({"id": AID[0], "asker": p[0], "mint": p[1],
                                   "chain": p[2], "ask_post_id": p[3],
                                   "price": p[5], "mcap": p[6],
                                   "status": "asked"})
                self.rows = [(AID[0],)]
        elif "FROM asks WHERE asker" in n:
            open_ = [r for r in DB["asks"]
                     if r["asker"] == p[0] and r["status"] == "asked"]
            open_.sort(key=lambda r: -r["id"])
            self.rows = [(r["id"], r["mint"], r["chain"], r["price"],
                          r["mcap"]) for r in open_[:1]]
        elif "SELECT id FROM callers" in n:
            self.rows = [(r["id"],) for r in DB["callers"]
                         if r["handle"] == p[0]]
        elif "INSERT INTO callers" in n:
            DB["callers"].append({"id": len(DB["callers"]) + 1,
                                  "handle": p[0]})
            self.rows = [(len(DB["callers"]),)]
        elif "INSERT INTO calls" in n:
            kind = "'hinted'" if "'hinted'" in n else "'asked'"
            DB["calls"].append({"coin": p[1], "price": p[4], "kind": kind})
            self.rows = []
        elif "status = 'confirmed'" in n:
            for r in DB["asks"]:
                if r["id"] == p[0]:
                    r["status"] = "confirmed"
            self.rows = []
        elif "status = 'expired'" in n:
            n_exp = 0
            for r in DB["asks"]:
                if r.get("status") == "asked":
                    r["status"] = "expired"
                    n_exp += 1
            self.rowcount = n_exp
            self.rows = []
        elif "SELECT id FROM submissions" in n:
            self.rows = []
        elif "INSERT INTO submissions" in n:
            DB["subs"].append(p[1])
            self.rows = [(len(DB["subs"]),)]
        else:
            self.rows = []

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class Conn:
    def cursor(self):
        return Cur()

    def commit(self):
        pass


import listener.askconfirm as ac  # noqa: E402
import listener.milestones as ms  # noqa: E402
import listener.weekly as wk  # noqa: E402
from brain.derive import crown  # noqa: E402
from brain.hints import is_hint, resolve, file_hinted  # noqa: E402
from brain.snapshotter import crossings  # noqa: E402

conn = Conn()
say = lambda who, t: print(f"  @{who}: {t}")

print("ACT 1 — the ask. meme popping, 400 likes, CA in parent.")
a = ac.handle_ask(conn, "MEME", "ask1", "0xabc", "par9")
say("urdheim", a["text"])
assert DB["asks"][0]["price"] == 0.001

print("ACT 2 — confirm. asker says got in (claims wrong number).")
c = ac.handle_confirm(conn, "MEME", "got in early at 20k!!")
say("urdheim", c["text"])
assert DB["calls"][0]["price"] == 0.001, "chain, not 20k"
assert DB["calls"][0]["kind"] == "'asked'"

print("ACT 3 — silence. ghost asks, never replies, lapses.")
ac.handle_ask(conn, "ghost", "ask2", "0xabc")
assert ac.expire(conn) == 1 and len(DB["calls"]) == 1

print("ACT 4 — milestones. price 4x's, snapshotter flags, quote fires.")
PRICE["p"] = 0.004
assert crossings({}, 4.0) == [3]
ms.quote = lambda pid, text, dry=True, allow_live=False: {"dry": True}
print(f"  snapshotter: MILESTONE 3x | quote (dry): "
      f"{ms.fmt_quote('MEME', 'MEME', 3, 1)[:60]}…")

print("ACT 5 — friday. weekly board posts.")
wk.post = lambda text, dry=True, allow_live=False: {"dry": True}
w = wk.fmt_week([{"handle": "MEME", "calls": 1, "best_x": 4.0}])
print("  " + w.replace("\n", "\n  "))
assert len(w) <= 280

print("ACT 6 — derivation. three $MEME coins, numbers crown.")
cands = [
    {"mint": "0xabc", "chain": "robinhood", "symbol": "MEME", "liq": 90000, "vol_h24": 400000,
     "txns_h24": 8000, "age_min": 300},
    {"mint": "0xcopy", "chain": "robinhood", "symbol": "MEME", "liq": 800, "vol_h24": 2000,
     "txns_h24": 60, "age_min": 40},
    {"mint": "0xdead", "chain": "solana", "symbol": "MEMECOIN", "liq": 100, "vol_h24": 300,
     "txns_h24": 9, "age_min": 10}]
r = crown(cands, keywords=["meme"])
assert r["leader"]["mint"] == "0xabc", r
print(f"  crown: 0xabc leads, {len(r['contenders'])} contenders")

print("ACT 7 — soft shill. milla hints, solo pool, proposed only.")
t = is_hint("@urdheim $MEME is loading hard")
lead = resolve(t, pools=cands)
h = file_hinted(conn, "milla", t, lead, "p9")
say("urdheim", h["text"])
assert DB["calls"][-1]["kind"] == "'hinted'"
assert DB["calls"][-1]["price"] is None

print("\nSIMULATION CLEAN: 7 acts, 0 tweets sent, 0 wrong CAs.")
print(f"db: asks={len(DB['asks'])} calls={len(DB['calls'])} "
      f"subs={len(DB['subs'])}")
