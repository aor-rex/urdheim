"""Phase-6 tests. No network: pools injected, conn faked."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.hints import is_hint, resolve, file_hinted  # noqa: E402

# --- detection ---
assert is_hint("@urdheim $MERRYMEN is loading hard") == "MERRYMEN"
assert is_hint("sleeping on $DOGE fr") == "DOGE"
assert is_hint("@urdheim track this 0xabc") is None  # tag flow, not hint
assert is_hint("ca?") is None
assert is_hint("loving $BTC today") is None  # no bull word
assert is_hint("loading 0xa15cd06dd305269a0f48bebeb30aa3588fba7b32") is None
print("is_hint: 6/6 pass")

# --- resolve: one pool wins, ties and empties refuse ---
solo = [{"mint": "0xsolo", "chain": "robinhood", "symbol": "MERRYMEN",
         "liq": 90000, "vol_h24": 400000, "txns_h24": 8000, "age_min": 300}]
assert resolve("MERRYMEN", pools=solo)["mint"] == "0xsolo"
assert resolve("MERRYMEN", pools=[]) is None
tie = [dict(solo[0]),
       {"mint": "0xcopy", "chain": "robinhood", "symbol": "MERRYMEN",
        "liq": 91000, "vol_h24": 405000, "txns_h24": 8100, "age_min": 310}]
assert resolve("MERRYMEN", pools=tie) is None, "copycat tie must refuse"
print("resolve: solo wins, empty/tie refuse")

# --- filing: hinted kind, proposed phrasing, dupe-safe ---
calls = []


class FakeCur:
    def __init__(self):
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        if "FROM callers" in q:
            self._row = None  # new poster
        elif "INSERT INTO callers" in q:
            self._row = (1,)
        elif "INSERT INTO calls" in q:
            calls.append((q, p))
            self._row = None

    def fetchone(self):
        return self._row


class FakeConn:
    def cursor(self):
        return FakeCur()

    def commit(self):
        pass


h = file_hinted(FakeConn(), "milla", "MERRYMEN", solo[0], "p123")
q, row = calls[0]
assert "'hinted'" in q, q  # kind is a SQL literal, 8 placeholders
assert row[1] == "MERRYMEN" and row[2] == "0xsolo"
assert row[4] is None, "no entry claimed on a hint"
assert "hinted" in h["text"] or "proposed" in h["text"], h
assert "not a call" in h["text"] or "proposed only" in h["text"], h
assert len(h["text"]) <= 280
print("file_hinted: kind + phrasing honest")
print("hints phase-6: all pass")
