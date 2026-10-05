"""Heimdall poster jobs: read postgres, shape tweets, post via uny-x poster
shell, log tweet ids back. Thin reader of the DB with a posting hand.

Usage: python3 poster/heimdall.py flop|listing|siren|recap [--dry]
--dry prints instead of posting.
"""
import os
import subprocess
import sys

import psycopg


def db():
    return psycopg.connect(os.environ["DB_URL"])


def flop(cur):
    cur.execute(
        """SELECT c.handle, cl.coin, cl.mint, cl.price_at_call, cl.post_url,
                  s.price AS now_price
           FROM calls cl JOIN callers c ON c.id = cl.caller_id
           LEFT JOIN LATERAL (SELECT price FROM snapshots s
                              WHERE s.call_id = cl.id
                              ORDER BY taken_at DESC LIMIT 1) s ON true
           WHERE cl.called_at > now() - interval '24 hours'
             AND s.price IS NOT NULL AND cl.price_at_call > 0
           ORDER BY (s.price - cl.price_at_call) / cl.price_at_call ASC
           LIMIT 1"""
    )
    r = cur.fetchone()
    if not r:
        return None
    handle, coin, mint, then, url, now = r
    pct = (now - then) / then * 100
    return (f"receipt of the day: @{handle} called ${coin} at {then:g}, "
            f"now {now:g} ({pct:+.0f}%). full record:")


def listing(cur):
    cur.execute(
        """SELECT handle FROM callers
           WHERE added_at > now() - interval '24 hours' ORDER BY added_at DESC LIMIT 1"""
    )
    r = cur.fetchone()
    if not r:
        return None
    return f"new caller on the board: @{r[0]}. every call from here gets a receipt."


def siren(cur):
    cur.execute(
        """SELECT c.handle, cl.coin, cl.mint, cl.post_url
           FROM calls cl JOIN callers c ON c.id = cl.caller_id
           JOIN LATERAL (SELECT price FROM snapshots s
                         WHERE s.call_id = cl.id
                         ORDER BY taken_at DESC LIMIT 1) s ON true
           WHERE cl.called_at > now() - interval '7 days'
             AND s.price < cl.price_at_call * 0.1
           ORDER BY cl.called_at DESC LIMIT 1"""
    )
    r = cur.fetchone()
    if not r:
        return None
    handle, coin, mint, url = r
    return (f"rug siren: ${coin} called by @{handle} is down 90%+ "
            f"from call. the receipt: {url}")


JOBS = {"flop": flop, "listing": listing, "siren": siren}


def post(text: str, dry: bool) -> str:
    if dry:
        print("[dry]", text, flush=True)
        return "dry"
    out = subprocess.run(
        ["python3", "-m", "unyx.cli", "post", text],
        capture_output=True, text=True, timeout=120,
        env={**os.environ,
             "UNYX_COOKIES": os.environ.get("POSTER_COOKIES", "")},
    )
    print(out.stdout.strip() or out.stderr.strip()[-300:], flush=True)
    return out.stdout.strip()


def main():
    job, dry = sys.argv[1], "--dry" in sys.argv
    with db() as conn, conn.cursor() as cur:
        text = JOBS[job](cur)
        if not text:
            print(f"{job}: nothing to post", flush=True)
            return
        tid = post(text, dry)
        if not dry:
            cur.execute(
                "INSERT INTO poster_log(job, text, tweet_id) VALUES (%s, %s, %s)",
                (job, text, tid),
            )
            conn.commit()


if __name__ == "__main__":
    main()
