"""Snapshotter: reprice open calls, track peaks, judge states.

One DexScreener read per call (free, no key). Writes a `snapshots` row,
updates `calls.peak/peak_x/state`. Peak decides the Xs on receipts and
the leaderboard (median, never best). State decides the seals.

States: open -> vindicated (peak >= 2x) | condemned (bled out or stale)
        any non-rugged -> rugged (liquidity pulled, checked first).
Rugged is terminal: the loop stops repricing those.

Thresholds env-tunable (see .env.example):
  SNAP_VINDICATE_X=2  SNAP_RUG_LIQ_USD=1000  SNAP_RUG_DROP=0.9
  SNAP_CONDEMN_DROP=0.5  SNAP_CONDEMN_DAYS=30

Run: DB_URL=... python brain/snapshotter.py [limit]
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg  # noqa: E402

from watcher.common import snapshot_price  # noqa: E402

VIND_X = float(os.environ.get("SNAP_VINDICATE_X", "2"))
RUG_LIQ = float(os.environ.get("SNAP_RUG_LIQ_USD", "1000"))
RUG_DROP = float(os.environ.get("SNAP_RUG_DROP", "0.9"))
CONDEMN_DROP = float(os.environ.get("SNAP_CONDEMN_DROP", "0.5"))
CONDEMN_DAYS = int(os.environ.get("SNAP_CONDEMN_DAYS", "30"))


def judge(entry, peak_x, now, liq, max_liq, called_at) -> str:
    """Rug first (onchain death beats market verdict), then glory, then rot."""
    if max_liq and liq < RUG_LIQ and (max_liq - liq) / max_liq >= RUG_DROP:
        return "rugged"
    if peak_x and peak_x >= VIND_X:
        return "vindicated"
    if entry and now and now < entry * CONDEMN_DROP:
        return "condemned"
    if called_at:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if (now_utc - called_at).days >= CONDEMN_DAYS and (
                not peak_x or peak_x < VIND_X):
            return "condemned"
    return "open"


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    with psycopg.connect(os.environ["DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, mint, chain, price_at_call, called_at
               FROM calls WHERE state <> 'rugged'
               ORDER BY called_at DESC LIMIT %s""", (limit,))
        rows = cur.fetchall()
        print(f"snap: {len(rows)} calls to reprice", flush=True)
        for cid, mint, chain, entry, called_at in rows:
            snap = snapshot_price(mint, chain)
            if not snap or not snap.get("price"):
                print(f"SKIP {cid} {mint[:10]} no pair on dexscreener",
                      flush=True)
                continue
            now, liq = snap["price"], snap.get("liq") or 0
            cur.execute(
                """INSERT INTO snapshots(call_id, price, mcap, liq)
                   VALUES (%s, %s, %s, %s)""",
                (cid, now, snap.get("mcap"), liq))
            cur.execute(
                """SELECT MAX(price), MAX(liq) FROM snapshots
                   WHERE call_id = %s""", (cid,))
            peak, max_liq = cur.fetchone()
            cur.execute(
                """SELECT taken_at FROM snapshots WHERE call_id = %s
                   ORDER BY price DESC, taken_at DESC LIMIT 1""", (cid,))
            peak_at = cur.fetchone()[0]
            peak_x = (peak / entry) if entry else None
            state = judge(entry, peak_x, now, liq, max_liq, called_at)
            cur.execute(
                """UPDATE calls SET peak = %s, peak_at = %s,
                                  peak_x = %s, state = %s
                   WHERE id = %s""", (peak, peak_at, peak_x, state, cid))
            px = f"{peak_x:.2f}x" if peak_x else "n/a"
            print(f"{state:10s} id={cid} peak_x={px} liq=${liq:,.0f}",
                  flush=True)
        conn.commit()
    print("snap: done", flush=True)


if __name__ == "__main__":
    main()
