"""Milestone quotes: when a tracked call crosses 3x/5x/10x, quote the
original tag post once per threshold. Never repeats (quoted_* flags).

Phrasing rotates deterministically by (call_id, milestone) so the 3x,
5x and 10x quotes on one call read differently. AI-varied phrasing
plugs in here later — same function signature, richer body.

Run: DB_URL=... python listener/milestones.py [--live]
Default is dry: prints what it WOULD quote. --live sends via outbox
(which still needs allow_live; pass --allow to actually tweet).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from listener.outbox import quote  # noqa: E402

TEMPLATES = [
    "called by @{caller} — ${coin} just hit {m}x. receipt below.",
    "@{caller} saw ${coin} early. that's {m}x now.",
    "${coin} at {m}x. @{caller} filed this one, ledger kept the receipt.",
    "another one for @{caller}: ${coin} {m}x from the call.",
    "@{caller}'s ${coin} call is sitting at {m}x. tracked, timestamped.",
    "{m}x on ${coin}. credit where due — @{caller} called it.",
]


def fmt_quote(handle: str, coin: str, m: int, call_id: int) -> str:
    tpl = TEMPLATES[(call_id + m) % len(TEMPLATES)]
    return tpl.format(caller=handle, coin=coin, m=m)


def due(conn) -> list:
    """Calls with a fresh unquoted crossing. Oldest first, 5 per run."""
    out = []
    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.id, c.coin, c.post_id, h.handle,
                      c.hit_3x, c.hit_5x, c.hit_10x,
                      c.quoted_3x, c.quoted_5x, c.quoted_10x
               FROM calls c JOIN callers h ON h.id = c.caller_id
               WHERE COALESCE(c.hidden, FALSE) = FALSE
                 AND ((c.hit_3x AND NOT c.quoted_3x)
                   OR (c.hit_5x AND NOT c.quoted_5x)
                   OR (c.hit_10x AND NOT c.quoted_10x))
               ORDER BY c.id LIMIT 5""")
        for cid, coin, pid, handle, h3, h5, h10, q3, q5, q10 in cur.fetchall():
            for m, hit, quoted in ((3, h3, q3), (5, h5, q5), (10, h10, q10)):
                if hit and not quoted:
                    out.append({"call_id": cid, "coin": coin,
                                "post_id": pid, "caller": handle, "m": m})
                    break  # one quote per call per run, lowest first
    return out


def run(conn, live: bool = False, allow: bool = False) -> list:
    done = []
    for d in due(conn):
        text = fmt_quote(d["caller"], d["coin"], d["m"], d["call_id"])
        res = quote(d["post_id"], text, dry=not live, allow_live=allow)
        if res.get("live"):
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE calls SET quoted_{d['m']}x = TRUE WHERE id = %s",
                    (d["call_id"],))
            conn.commit()
        done.append({**d, "text": text, "sent": bool(res.get("live")),
                     "dry": bool(res.get("dry"))})
        print(f"milestone {d['coin']} {d['m']}x dry={res.get('dry')}",
              flush=True)
    return done


def main() -> None:
    import psycopg
    live = "--live" in sys.argv
    allow = "--allow" in sys.argv
    with psycopg.connect(os.environ["DB_URL"]) as conn:
        run(conn, live=live, allow=allow)
    print("milestones: done", flush=True)


if __name__ == "__main__":
    main()
