"""Phase-4 tests. No DB, no network: conn stubbed, snapshot stubbed."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# stub watcher.common before askconfirm imports it lazily (module-level is
# fine too, but lazy import happens inside functions — stub the module)
wc = types.ModuleType("watcher.common")
wc.detect_chain = lambda m: "robinhood" if m.startswith("0x") else "solana"
wc.snapshot_price = lambda m, c=None: {"price": 0.001, "mcap": 50000.0,
                                       "symbol": "MEME", "liq": 9000.0}
wc.find_cas = lambda t: ["0xabc"] if "0xabc" in t else []
sys.modules["watcher"] = types.ModuleType("watcher")
sys.modules["watcher.common"] = wc

import listener.askconfirm as ac  # noqa: E402

# --- pure matchers ---
assert ac.is_ca_ask("ca?")
assert ac.is_ca_ask("CA")
assert ac.is_ca_ask("drop the ca")
assert ac.is_ca_ask("contract?")
assert not ac.is_ca_ask("track this 0xabc")
assert not ac.is_ca_ask("this is going to 100x, ca in bio")
assert ac.is_yes("got in at 50k")
assert ac.is_yes("aped hard")
assert ac.is_yes("YES")
assert not ac.is_yes("maybe later")
assert not ac.is_yes("ca?")
print("matchers: 10/10 pass")

# --- flow on a fake conn ---
TABLES = {"asks": [], "callers": [], "calls": []}


class FakeCur:
    def __init__(self):
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        qn = " ".join(q.split())
        if "INSERT INTO asks" in qn:
            if any(r["asker"] == p[0] and r["ask_post_id"] == p[3]
                   for r in TABLES["asks"]):
                self._rows = []  # conflict -> nothing returned
            else:
                r = {"id": len(TABLES["asks"]) + 1, "asker": p[0],
                     "mint": p[1], "chain": p[2], "ask_post_id": p[3],
                     "parent_post_id": p[4], "price": p[5], "mcap": p[6],
                     "status": "asked"}
                TABLES["asks"].append(r)
                self._rows = [(r["id"],)]
        elif "FROM asks WHERE asker" in qn:
            rows = [r for r in TABLES["asks"]
                    if r["asker"] == p[0] and r["status"] == "asked"]
            rows.sort(key=lambda r: -r["id"])
            self._rows = [(r["id"], r["mint"], r["chain"],
                           r["price"], r["mcap"]) for r in rows[:1]]
        elif "SELECT id FROM callers" in qn:
            self._rows = [(r["id"],) for r in TABLES["callers"]
                          if r["handle"] == p[0]]
        elif "INSERT INTO callers" in qn:
            r = {"id": len(TABLES["callers"]) + 1, "handle": p[0]}
            TABLES["callers"].append(r)
            self._rows = [(r["id"],)]
        elif "INSERT INTO calls" in qn:
            TABLES["calls"].append({"caller": p[0], "coin": p[1],
                                    "price": p[4], "kind": "asked"})
            self._rows = []
        elif "UPDATE asks SET status = 'confirmed'" in qn:
            for r in TABLES["asks"]:
                if r["id"] == p[0]:
                    r["status"] = "confirmed"
            self._rows = []
        elif "status = 'expired'" in qn:
            n = 0
            for r in TABLES["asks"]:
                if r["status"] == "asked":
                    r["status"] = "expired"
                    n += 1
            self.rowcount = n
            self._rows = []
        else:
            self._rows = []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class FakeConn:
    def cursor(self):
        return FakeCur()

    def commit(self):
        pass


conn = FakeConn()

# ask files interest with chain price
a = ac.handle_ask(conn, "MEME", "ask1", "0xabc", "par9")
assert a["price"] == 0.001 and a["mcap"] == 50000.0, a
assert "@MEME" in a["text"] and len(a["text"]) <= 280, a
assert TABLES["asks"][0]["status"] == "asked"

# dupe ask same post: idempotent, same asker not double-filed
a2 = ac.handle_ask(conn, "MEME", "ask1", "0xabc", "par9")
assert len(TABLES["asks"]) == 1, TABLES["asks"]

# non-yes reply confirms nothing, leaves ask open
assert ac.handle_confirm(conn, "MEME", "maybe later") is None
assert TABLES["asks"][0]["status"] == "asked"

# yes files confirmed receipt at ASK price, not reply text numbers
c = ac.handle_confirm(conn, "MEME", "got in at 20k mcap!!")
assert c and c["coin"] == "MEME", c
assert TABLES["calls"][0]["price"] == 0.001, TABLES["calls"]  # chain, not 20k
assert TABLES["calls"][0]["kind"] == "asked"
assert TABLES["asks"][0]["status"] == "confirmed"
assert "@MEME" in c["text"] and len(c["text"]) <= 280

# second yes with no open ask: nothing
assert ac.handle_confirm(conn, "MEME", "got in") is None

# expiry lapses the stragglers, never confirms
ac.handle_ask(conn, "ghost", "ask2", "0xabc")
assert ac.expire(conn) == 1
assert TABLES["asks"][1]["status"] == "expired"
assert len(TABLES["calls"]) == 1, "expiry must not file"

print("ask-confirm flow: 12/12 pass")
