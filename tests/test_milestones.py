"""Phase-2 tests. No DB, no network: conn and outbox.quote stubbed."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.snapshotter import crossings  # noqa: E402

# --- pure crossing logic ---
assert crossings({}, None) == []
assert crossings({}, 0.5) == []
assert crossings({}, 3.2) == [3]
assert crossings({"hit_3x": True}, 5.5) == [5]
assert crossings({"hit_3x": True, "hit_5x": True}, 12.0) == [10]
assert crossings({"hit_3x": True, "hit_5x": True, "hit_10x": True},
                 50.0) == []
# jump straight past two thresholds at once
assert crossings({}, 6.0) == [3, 5]
print("crossings: 7/7 pass")

# --- worker: due() picks unquoted, run() quotes lowest-first, marks sent ---
import listener.milestones as ms  # noqa: E402

ROWS = [
    # cid coin pid handle h3 h5 h10 q3 q5 q10
    (7, "MERRYMEN", "pid7", "ryu_ngmi",
     True, True, False, False, False, False),   # due: 3x first
    (8, "DUD", "pid8", "anon",
     False, False, False, False, False, False),  # nothing hit
    (9, "OLD", "pid9", "vet",
     True, False, False, True, False, False),    # already quoted
]


class FakeCur:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        self.q, self.p = q, p
        if q.strip().startswith("UPDATE"):
            for r in self.db.rows:
                if r[0] == p[0]:
                    idx = {"hit_3x": 4, "hit_5x": 5, "hit_10x": 6,
                           "quoted_3x": 7, "quoted_5x": 8,
                           "quoted_10x": 9}[q.split("SET ")[1].split(" ")[0]]
                    r[idx] = True

    def fetchall(self):
        return [tuple(r) for r in self.db.rows
                if (r[4] and not r[7]) or (r[5] and not r[8])
                or (r[6] and not r[9])]


class FakeConn:
    def __init__(self):
        self.rows = [list(r) for r in ROWS]

    def cursor(self):
        return FakeCur(self)

    def commit(self):
        pass


sent = []
ms.quote = lambda pid, text, dry=True, allow_live=False: (
    sent.append((pid, text)) or {"live": True} if (not dry and allow_live)
    else {"dry": True})

conn = FakeConn()
assert len(ms.due(conn)) == 1 and ms.due(conn)[0]["m"] == 3, "due picks 3x"

# dry run quotes nothing, marks nothing
done = ms.run(conn, live=False)
assert done[0]["dry"] and sent == [], done
assert conn.rows[0][7] is False, "dry must not mark quoted"

# live run quotes 3x and marks only quoted_3x
done = ms.run(conn, live=True, allow=True)
assert done[0]["sent"] and len(sent) == 1, (done, sent)
assert sent[0][0] == "pid7", sent  # url append covered in test_outbox
assert conn.rows[0][7] is True and conn.rows[0][8] is False, conn.rows[0]

# next run picks 5x for the same call (varied text)
done2 = ms.run(conn, live=True, allow=True)
assert done2[0]["m"] == 5 and done2[0]["text"] != done[0]["text"], done2

# phrasing under 280 and mentions caller
for d in done + done2:
    assert len(d["text"]) <= 280 and "@ryu_ngmi" in d["text"], d

print("milestones worker: 8/8 pass")
