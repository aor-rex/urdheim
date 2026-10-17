"""Meme watch: a viral meme with no coin yet. Remember it, recheck daily,
file hinted the moment a pool clears traction. Never files without a
real pool; dies silent after 7 days.

Open path runs inside the listen loop (immediate reply). Recheck runs
daily from the snap loop: dry unless --live --allow, same as milestones.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

WATCH_DAYS = int(os.environ.get("WATCH_DAYS", "7"))
WATCH_CAP = int(os.environ.get("WATCH_CAP", "50"))
RECHECK_LIMIT = 20


def _words(desc: str) -> list:
    out = []
    for w in (desc or "").split():
        w = w.strip(".,!?#@:").lower()
        if len(w) > 2 and w not in out:
            out.append(w)
        if len(out) >= 12:
            break
    return out


def try_pool(keywords: list) -> dict | None:
    """Immediate search: any keyword with a pool that crowns, wins."""
    from brain.derive import crown
    from brain.hints import search_pools
    pools, seen = [], set()
    for kw in (keywords or [])[:5]:
        for p in search_pools(kw):
            if p.get("mint") not in seen:
                seen.add(p.get("mint"))
                pools.append(p)
    if not pools:
        return None
    return crown(pools, keywords=keywords or [])["leader"]


def handle_meme(conn, png: bytes, post_id: str, reporter: str,
                seed: list | None = None) -> str | None:
    """One meme image: pool now -> hinted reply; else watch + radar reply.
    Dupe image -> silence."""
    from brain.derive import describe_image, dhash
    from brain.hints import file_hinted
    if not png:
        return None
    try:
        img_hash = "%016x" % dhash(png)
    except Exception:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM meme_watches WHERE image_hash = %s",
                    (img_hash,))
        if cur.fetchone():
            return None  # already watched (or filed) — silence, not a dupe
    desc = describe_image(png) or ""
    keywords = list(seed or []) + [w for w in _words(desc)
                                   if w not in (seed or [])]
    lead = try_pool(keywords)
    if lead:
        h = file_hinted(conn, reporter, lead.get("symbol") or "?",
                        lead, post_id)
        return h["text"]
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM meme_watches WHERE status='watching'")
        n = (cur.fetchone() or (0,))[0]
        if n >= WATCH_CAP:
            cur.execute("""DELETE FROM meme_watches WHERE id IN
                           (SELECT id FROM meme_watches WHERE status='watching'
                            ORDER BY opened_at ASC LIMIT 1)""")
        cur.execute(
            """INSERT INTO meme_watches
                 (image_hash, keywords, description, post_id, reporter,
                  expires_at)
               VALUES (%s, %s, %s, %s, %s, now() + (%s || ' days')::interval)
               ON CONFLICT (image_hash) DO NOTHING""",
            (img_hash, " ".join(keywords), desc[:200], post_id, reporter,
             str(WATCH_DAYS)))
        conn.commit()
    first = (seed or [None])[0]
    what = f"${first} " if first else "meme "
    return (f"@{reporter} {what}on the radar — "
            f"watching for a pool. not a call.")[:280]


def recheck(conn, dry: bool = True,
            allow_live: bool = False) -> dict:
    """Daily pass: expire the dead, file what cleared traction. Returns
    {expired, watched, filed}."""
    from brain.hints import file_hinted
    from listener.outbox import quote
    out = {"expired": 0, "watched": 0, "filed": 0}
    with conn.cursor() as cur:
        cur.execute("UPDATE meme_watches SET status='expired' "
                    "WHERE status='watching' AND expires_at < now()")
        out["expired"] = cur.rowcount or 0
        conn.commit()
        cur.execute("""SELECT id, keywords, post_id, reporter
                       FROM meme_watches WHERE status='watching'
                       ORDER BY opened_at ASC LIMIT %s""", (RECHECK_LIMIT,))
        rows = cur.fetchall()
    out["watched"] = len(rows)
    for wid, keywords, post_id, reporter in rows:
        try:
            lead = try_pool((keywords or "").split())
        except Exception:
            continue
        if not lead:
            continue
        h = file_hinted(conn, reporter or "watcher",
                        lead.get("symbol") or "?", lead, post_id or "")
        with conn.cursor() as cur:
            cur.execute("UPDATE meme_watches SET status='filed' WHERE id=%s",
                        (wid,))
            conn.commit()
        out["filed"] += 1
        if post_id:
            print(quote(post_id, h["text"], dry=dry,
                        allow_live=allow_live), flush=True)
        else:
            print(f"watch filed: {h['text'][:120]}", flush=True)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--allow", action="store_true")
    a = ap.parse_args()
    from listener.mentions import db
    conn = db()
    if conn is None:
        print("db: none (no DB_URL)", flush=True)
        return
    print(recheck(conn, dry=not a.live, allow_live=a.allow), flush=True)
    conn.close()


if __name__ == "__main__":
    main()
