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
        raise SystemExit("listener: no cookies — set LISTENER_COOKIES to a file")
    if not c.login_from_cookies(cookies):
        raise SystemExit("listener: cookie login failed")
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


def fetch_mentions(n: int = 20) -> list[dict]:
    """uny-x mentions -> normalized list. Free, cookie session."""
    with client() as c:
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
            arrow = " 📈" if now > then else " 📉"
        lines.append(f"@{handle} called {coin} @ ${then:.8g}{arrow}")
    perf = ""
    if now and rows[0][2]:
        pct = (now - rows[0][2]) / rows[0][2] * 100
        perf = f" since first call: {pct:+.0f}%"
    return "receipt 🧾\n" + "\n".join(lines) + f"\nnow ${now:.8g}{perf}" if now else "receipt 🧾\n" + "\n".join(lines)


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
    except Exception as e:
        return f"couldn't track @{handle} — db unreachable ({str(e)[:80]})"
    return (f"tracking @{handle} — on the watchlist. "
            f"first card lands at urdheim/profile/{handle} once calls land.")


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
    return f"logged — watching {short}. receipt follows once the call resolves."


def execute(author: str, text: str, conn, post_id: str = "") -> str | None:
    """Brain intent -> action. Returns reply text or None (silence)."""
    intent = classify_mention(author, text)
    kind, handle, mint = intent["intent"], intent["handle"], intent["mint"]
    if handle.lower() == SELF:
        handle = ""
    if kind == "ignore":
        return None
    if kind == "receipt_coin":
        m = mint or next(iter(CA_RE.findall(text or "")), "")
        return coin_receipt(conn, m) if m else None
    if kind == "receipt_caller":
        return caller_file(conn, handle) if handle else None
    if kind == "track_caller":
        return enroll_caller(handle) if handle else None
    if kind == "track_call":
        m = mint or next(iter(CA_RE.findall(text or "")), "")
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
            raise SystemExit("listener: no cookies for getxapi fallback either")
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
    for m in fetch_mentions():
        if m["id"] in seen or not m["id"]:
            continue
        seen.add(m["id"])
        reply = execute(m["author"], m["text"], conn, m["id"])
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
