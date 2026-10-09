"""Urdheim mentions listener: tags in -> brain decides -> executor acts.

Polls `unyx mentions` (free, same cookies). Every mention goes to
brain/intent.py (model reads conversation, returns structured intent);
this file only executes: receipts, track enrollment, or silence.
Reply path: `unyx reply` free first, GetXAPI $0.002 fallback (budget-guarded).
Seen ids in listener/seen.json — restarts never double-reply.
Track enrollments land in the watched table (callers) + submissions table.

Usage:
  mentions.py --once [--dry] [--test "@user check <mint>"]
  mentions.py --loop [--interval 300]
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unyx import UnyxClient  # noqa: E402

from brain.intent import classify_mention  # noqa: E402
from watcher.common import detect_chain, snapshot_price  # noqa: E402

CA_RE = re.compile(r"0x[0-9a-fA-F]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}")
SELF = os.environ.get("LISTENER_SELF", "urdheim").lower()


def client() -> UnyxClient:
    """One session per poll batch. LISTENER_COOKIES wins, UNYX_COOKIES
    next. No local default: in containers the dev-box path doesn't exist."""
    c = UnyxClient()
    cookies = os.environ.get("LISTENER_COOKIES", "") or os.environ.get(
        "UNYX_COOKIES", "")
    if not cookies:
        raise RuntimeError("listener: no cookies — set LISTENER_COOKIES to a file")
    if not c.login_from_cookies(cookies):
        raise RuntimeError("listener: cookie login failed")
    return c


def seen_path() -> str:
    return os.environ.get("SEEN_PATH",
                          os.path.join(os.path.dirname(__file__), "seen.json"))


def load_seen() -> set:
    p = seen_path()
    if os.path.exists(p):
        try:
            return set(json.load(open(p)))
        except Exception:
            return set()
    return set()


def save_seen(ids: set) -> None:
    json.dump(sorted(ids), open(seen_path(), "w"))


def parse_raw_tweet(raw: dict) -> dict | None:
    """Pull (id, author, text, reply_to) out of a TweetResultByRestId blob."""
    try:
        res = (raw.get("data", {}).get("tweetResult", {}).get("result", {})
               or raw.get("result", {}))
        if res.get("__typename") == "TweetWithVisibilityResults":
            res = res.get("tweet", {})
        leg = res.get("legacy", {})
        user = (res.get("core", {}).get("user_results", {}).get("result", {}))
        uleg = user.get("legacy", {})
        text = leg.get("full_text", "") or ""
        if not text and not leg.get("id_str"):
            return None
        return {"id": leg.get("id_str") or res.get("rest_id", ""),
                "author": uleg.get("screen_name", "") or "?",
                "text": text,
                "reply_to": leg.get("in_reply_to_status_id_str", "") or ""}
    except (KeyError, TypeError, AttributeError):
        return None


def parent_context(c, mention_id: str) -> dict | None:
    """Bare 'track this' -> the post it replies to (author + text). Free reads."""
    try:
        m = parse_raw_tweet(c.read(mention_id).get("raw", {}))
    except Exception:
        return None
    if not m or not m["reply_to"]:
        return None
    try:
        p = parse_raw_tweet(c.read(m["reply_to"]).get("raw", {}))
    except Exception:
        return None
    return p


def fetch_mentions(n: int = 20, c=None) -> list[dict]:
    """uny-x mentions -> normalized list. Free, cookie session."""
    if c is None:
        with client() as fresh:
            data = fresh.mentions(n)
    else:
        data = c.mentions(n)
    items = []
    for m in data.get("mentions", []):
        user = m.get("user") or {}
        items.append({
            "id": str(m.get("id", "")),
            "author": user.get("screen_name", "") or "",
            "text": m.get("text", "") or "",
        })
    return items


def db():
    """psycopg conn or None (test mode runs without a DB)."""
    url = os.environ.get("DB_URL", "")
    if not url:
        return None
    import psycopg
    return psycopg.connect(url)


def coin_receipt(conn, mint: str) -> str | None:
    chain = detect_chain(mint)
    rows = []
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.handle, k.coin, k.price_at_call, k.called_at
                   FROM calls k JOIN callers c ON c.id = k.caller_id
                   WHERE k.mint = %s ORDER BY k.called_at DESC LIMIT 5""",
                (mint,))
            rows = cur.fetchall()
    if not rows:
        snap = snapshot_price(mint, chain)
        if not snap:
            return None
        return (f"no tracked calls on this coin yet. live: "
                f"${snap['price']:.8g} | mcap ${snap['mcap']:,.0f} ({chain})")
    snap = snapshot_price(mint, chain) or {}
    now = snap.get("price")
    lines = []
    for handle, coin, then, _ in rows:
        arrow = ""
        if now and then:
            arrow = " ▲" if now > then else " ▼"
        lines.append(f"@{handle} called {coin} @ ${then:.8g}{arrow}")
    perf = ""
    if now and rows[0][2]:
        pct = (now - rows[0][2]) / rows[0][2] * 100
        perf = f" since first call: {pct:+.0f}%"
    return "receipt\n" + "\n".join(lines) + f"\nnow ${now:.8g}{perf}" if now else "receipt\n" + "\n".join(lines)


def caller_file(conn, handle: str) -> str | None:
    if not conn:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM callers WHERE handle = %s", (handle,))
        row = cur.fetchone()
        if not row:
            return f"@{handle} is not tracked yet. nominate: urdheim/snitch"
        cur.execute("SELECT COUNT(*), MAX(called_at) FROM calls WHERE caller_id = %s",
                    (row[0],))
        total, last = cur.fetchone()
    return (f"@{handle}: {total or 0} calls on record"
            + (f", last {str(last)[:10]}" if last else "")
            + f" · full file: urdheim/profile/{handle}")


def load_seeds() -> list[str]:
    """Watchlist from the watched table. DB down → the 3 defaults, never a file."""
    try:
        conn = db()
        if conn is None:
            return ["degenreck", "devvaintnohobby", "Tally__DE"]
        with conn, conn.cursor() as cur:
            cur.execute("SELECT handle FROM watched WHERE active ORDER BY added_at")
            rows = [r[0] for r in cur.fetchall()]
            conn.close()
            if rows:
                return rows
    except Exception:
        pass
    return ["degenreck", "devvaintnohobby", "Tally__DE"]


def enroll_caller(handle: str) -> str:
    """track_caller executor: insert into watched (next poll backfills)."""
    try:
        conn = db()
        if conn is None:
            return f"couldn't track @{handle} — db unreachable (no DB_URL)"
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO watched (handle, source) VALUES (%s, 'enroll') "
                "ON CONFLICT (handle) DO UPDATE SET active = TRUE",
                (handle,))
            conn.commit()
        conn.close()
    except Exception as e:
        return f"couldn't track @{handle} — db unreachable ({str(e)[:80]})"
    return (f"tracking @{handle} — on the watchlist. "
            f"first card lands at urdheim/profile/{handle} once calls land.")


def filed_reply(caller: str, mint: str) -> str:
    """Full receipt line: ticker + caller + CA + entry price + mcap.

    Priced live at file time so the reply stands alone. Falls back to
    the bare watch line when the pricer comes back empty. Stays <280."""
    short = mint[:8] + "…" + mint[-4:] if len(mint) > 12 else mint
    base = os.environ.get("APP_URL", "https://urdheim.zone.id").rstrip("/")
    try:
        from watcher.common import snapshot_price, detect_chain
        snap = snapshot_price(mint, detect_chain(mint)) or {}
    except Exception:
        snap = {}
    price, mcap, sym = snap.get("price"), snap.get("mcap") or 0, snap.get("symbol") or ""
    if not price:
        return (f"logged @{caller}'s call — {short}. "
                f"receipt: {base}/profile/{caller}")
    ptxt = f"{price:.10f}".rstrip("0").rstrip(".")  # 0.00002812, not 2.8e-05
    tick = f"${sym} " if sym else ""
    return (f"logged {tick}@{(caller or '')[:20]} — {short} "
            f"@ ${ptxt} | mcap ${mcap:,.0f} · "
            f"{base}/profile/{caller}")[:280]


def enroll_call(conn, author: str, mint: str, post_id: str) -> str:
    """track_call executor: log to submissions (detective picks it up)."""
    if conn and post_id and post_id != "test-mode-no-id":
        url = f"https://x.com/i/status/{post_id}"
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM submissions WHERE post_url = %s", (url,))
            if not cur.fetchone():
                cur.execute(
                    """INSERT INTO submissions (post_url, suggested_caller,
                                                reporter_ip, status)
                       VALUES (%s, %s, %s, 'pending')""",
                    (url, f"{author}:{mint}", "x-mention"))
                conn.commit()
    short = mint[:10] + "…" if len(mint) > 12 else mint
    return filed_reply(author, mint)


def is_allowed(conn, author: str) -> bool:
    """Signed-in handles only. No conn (tests) -> closed, no one passes."""
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM allowed_users WHERE handle = %s",
                        (author.lower(),))
            return cur.fetchone() is not None
    except Exception:
        return False


def signin_nudge(conn, author: str) -> str | None:
    """One invite per stranger, then silence (protects the 7/day reply cap)."""
    base = os.environ.get("APP_URL", "https://urdheim.xyz").rstrip("/")
    msg = (f"hey @{author} — @urdheim is private. "
           f"sign in to use it: {base}/signin")
    if conn is None:
        return msg
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT nudged FROM allowed_users WHERE handle = %s",
                        (author.lower(),))
            row = cur.fetchone()
            if row and row[0]:
                return None  # already invited — silence from here on
            cur.execute(
                "INSERT INTO allowed_users (handle, nudged) VALUES (%s, TRUE) "
                "ON CONFLICT (handle) DO UPDATE SET nudged = TRUE",
                (author.lower(),))
            conn.commit()
    except Exception:
        return msg
    return msg


def execute(author: str, text: str, conn, post_id: str = "",
            c=None) -> str | None:
    """Brain intent -> action. Returns reply text or None (silence)."""
    if not is_allowed(conn, author):
        return signin_nudge(conn, author)
    intent = classify_mention(author, text)
    kind, handle, mint = intent["intent"], intent["handle"], intent["mint"]
    if handle.lower() == SELF:
        handle = ""
    if kind == "ignore":
        return None
    if kind == "receipt_coin":
        m = mint or next(iter(CA_RE.findall(text or "")), "")
        if not m and c is not None and post_id and post_id != "test-mode-no-id":
            parent = parent_context(c, post_id)
            if parent:
                m = next(iter(CA_RE.findall(parent["text"] or "")), "")
        return coin_receipt(conn, m) if m else None
    if kind == "receipt_caller":
        return caller_file(conn, handle) if handle else None
    if kind == "track_caller":
        return enroll_caller(handle) if handle else None
    if kind == "track_call":
        m = mint or next(iter(CA_RE.findall(text or "")), "")
        if not m and c is not None and post_id and post_id != "test-mode-no-id":
            parent = parent_context(c, post_id)
            if parent:
                m = next(iter(CA_RE.findall(parent["text"] or "")), "")
                if m:
                    return enroll_call(conn, parent["author"], m,
                                       parent["id"])
            return ("can't tell which call you mean — "
                    "reply with the CA and i'll log it.")
        return enroll_call(conn, author, m, post_id) if m else None
    return None


def send_reply(post_id: str, text: str, dry: bool = False) -> dict:
    if dry:
        return {"dry": True, "post_id": post_id, "chars": len(text)}
    try:
        with client() as c:
            out = c.reply(post_id, text)
        return {"via": "uny-x", "out": out}
    except Exception as e:
        # fallback: GetXAPI reply (budget-guarded, $0.002)
        from poster.getxapi import post as gx_post  # type: ignore
        cookies = os.environ.get("LISTENER_COOKIES", "")
        if not cookies:
            raise RuntimeError("listener: no cookies for getxapi fallback either")
        out = gx_post(text, cookies)
        return {"via": f"getxapi-fallback (uny-x: {str(e)[:100]})",
                "out": out}


def run_once(dry: bool = False, test: str = "") -> None:
    seen = load_seen()
    conn = db()
    if test:
        m = re.match(r"@(\w+)\s+(.*)", test)
        author, text = (m.group(1), m.group(2)) if m else ("tester", test)
        reply = execute(author, text, conn, "test-mode-no-id")
        print(f"TEST mention @{author}: {text[:80]}")
        print("DECISION:", (reply or "SILENCE")[:400])
        return
    try:
        found = fetch_mentions()
    except Exception as e:
        print(f"mentions fetch failed: {str(e)[:150]}", flush=True)
        found = []
    print(f"mentions: {len(found)}", flush=True)
    for m in found:
        if m["id"] in seen or not m["id"]:
            continue
        seen.add(m["id"])
        try:
            # no CA in the mention -> open a session so execute() can read
            # the parent post (track this / what's this / get this).
            if (not CA_RE.search(m["text"] or "")
                    and m["id"] and m["id"] != "test-mode-no-id"):
                with client() as c:
                    reply = execute(m["author"], m["text"], conn, m["id"], c)
            else:
                reply = execute(m["author"], m["text"], conn, m["id"])
        except Exception as e:
            print(f"mention skip @{m['author']}: {str(e)[:120]}")
            continue
        if not reply:
            print(f"ignore @{m['author']}: {(m['text'] or '')[:60]}")
            continue
        if dry:
            print(f"WOULD REPLY @{m['author']}: {reply[:200]}")
        else:
            print(send_reply(m["id"], reply))
    save_seen(seen) if not dry else None
    if conn:
        conn.close()


def main() -> None:
    dry = "--dry" in sys.argv
    test = ""
    for a in sys.argv[1:]:
        if a.startswith("--test="):
            test = a.split("=", 1)[1]
    if "--loop" in sys.argv:
        interval = 300
        for a in sys.argv[1:]:
            if a.startswith("--interval="):
                interval = int(a.split("=", 1)[1])
        while True:
            try:
                run_once(dry)
            except Exception as e:
                print("loop error:", str(e)[:150])
            time.sleep(interval)
    else:
        run_once(dry, test)


if __name__ == "__main__":
    main()
