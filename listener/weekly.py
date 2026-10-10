"""Weekly board: top callers of the last 7 days, posted Fridays.

Ranks by calls filed that week, best multiple breaks ties. One post,
top 3, each line handle + calls + best x. Links to the board — full
table lives on site, the post is the trailer.

Run: DB_URL=... python listener/weekly.py [--live] [--allow]
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from listener.outbox import post  # noqa: E402

SITE = os.environ.get("NEXT_PUBLIC_SITE", "https://urdheim.zone.id")


def top_week(conn, limit: int = 3) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT h.handle, COUNT(c.id) AS n,
                      COALESCE(MAX(c.peak_x), 0) AS best
               FROM callers h JOIN calls c ON c.caller_id = h.id
               WHERE c.called_at > now() - interval '7 days'
                 AND COALESCE(c.hidden, FALSE) = FALSE
               GROUP BY h.handle
               ORDER BY n DESC, best DESC LIMIT %s""", (limit,))
        return [{"handle": r[0], "calls": r[1], "best_x": r[2]}
                for r in cur.fetchall()]


def fmt_week(rows: list) -> str:
    week = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d")
    lines = [f"top callers this week ({week}):"]
    medals = ["1.", "2.", "3."]
    for i, r in enumerate(rows):
        best = f" · {r['best_x']:.1f}x best" if r["best_x"] else ""
        lines.append(
            f"{medals[i]} @{r['handle']} — "
            f"{r['calls']} call{'s' if r['calls'] != 1 else ''}{best}")
    lines.append(f"full board: {SITE}/leaderboard")
    return "\n".join(lines)


def run(conn, live: bool = False, allow: bool = False) -> dict:
    rows = top_week(conn)
    if not rows:
        print("weekly: no calls this week, nothing to post", flush=True)
        return {"posted": False, "reason": "empty week"}
    text = fmt_week(rows)
    res = post(text, dry=not live, allow_live=allow)
    print(f"weekly: dry={res.get('dry')} chars={len(text)}", flush=True)
    return {"posted": bool(res.get("live")), "dry": bool(res.get("dry")),
            "text": text}


def main() -> None:
    import psycopg
    live = "--live" in sys.argv
    allow = "--allow" in sys.argv
    with psycopg.connect(os.environ["DB_URL"]) as conn:
        run(conn, live=live, allow=allow)
    print("weekly: done", flush=True)


if __name__ == "__main__":
    main()
