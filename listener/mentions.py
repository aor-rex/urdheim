"""Urdheim mentions listener: tags in -> receipts out.

Polls `unyx mentions` (free, same cookies), answers only what it can:
  tag contains a CA/mint  -> coin receipt (calls + latest snapshot)
  tag contains an @handle -> caller file summary (record, worst call)
  anything else           -> ignored, logged, never replied to

Reply path: `unyx reply` free first, GetXAPI $0.002 fallback (budget-guarded).
Seen ids in listener/seen.json — restarts never double-reply.

Usage:
  mentions.py --once [--dry] [--test "@user check <mint>"]
  mentions.py --loop [--interval 300]
"""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from watcher.common import detect_chain, snapshot_price  # noqa: E402

HANDLE_RE = re.compile(r"@([A-Za-z0-9_]{1,15})")
CA_RE = re.compile(r"0x[0-9a-fA-F]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}")
SELF = os.environ.get("LISTENER_SELF", "ryu_ngmi").lower()

UNYX = ["/opt/data/projects/uny-x/.venv/bin/python", "-m", "unyx.cli"]
UNYX_DIR = "/opt/data/projects/uny-x"


def seen_path() -> str:
    return os.path.join(os.path.dirname(__file__), "seen.json")


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
    r = subprocess.run(UNYX + ["mentions", "-n", str(n)],
                       capture_output=True, text=True, cwd=UNYX_DIR,
                       timeout=120)
    out = r.stdout[r.stdout.find("{"):] if "{" in r.stdout else "{}"
    data = json.loads(out or "{}")
    items = []
    for m in data.get("mentions", []):
        author = m.get("author") or m.get("user") or {}
        if isinstance(author, dict):
            author = author.get("screen_name") or author.get("username") or ""
        items.append({
            "id": str(m.get("id", "")),
            "author": author,
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
        cur.execute(
            "SELECT id, verdict, total_calls FROM callers WHERE handle = %s",
            (handle,))
        row = cur.fetchone()
    if not row:
        return f"@{handle} is not tracked yet. nominate: urdheim/snitch"
    cid, verdict, total = row
    return (f"@{handle}: {verdict or 'unscored'} · "
            f"{total or 0} calls on record · full file: urdheim/caller/{handle}")


def decide(text: str, conn) -> str | None:
    """Tag text -> reply text, or None (stay silent)."""
    mints = list(dict.fromkeys(CA_RE.findall(text or "")))
    if mints:
        return coin_receipt(conn, mints[0])
    for h in HANDLE_RE.findall(text or ""):
        if h.lower() == SELF:
            continue
        out = caller_file(conn, h)
        if out:
            return out
    return None


def send_reply(post_id: str, text: str, dry: bool = False) -> dict:
    if dry:
        return {"dry": True, "post_id": post_id, "chars": len(text)}
    r = subprocess.run(UNYX + ["reply", post_id, text],
                       capture_output=True, text=True, cwd=UNYX_DIR,
                       timeout=120)
    if r.returncode == 0:
        return {"via": "uny-x", "out": r.stdout[-200:]}
    # fallback: GetXAPI reply (budget-guarded, $0.002)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "poster"))
    from getxapi import post as gx_post  # type: ignore
    out = gx_post(text, os.environ.get("LISTENER_COOKIES",
                  "/opt/data/projects/uny-x/cookies.json"))
    return {"via": "getxapi-fallback", "out": out}


def run_once(dry: bool = False, test: str = "") -> None:
    seen = load_seen()
    conn = db()
    if test:
        m = re.match(r"@(\w+)\s+(.*)", test)
        author, text = (m.group(1), m.group(2)) if m else ("tester", test)
        reply = decide(text, conn)
        print(f"TEST mention @{author}: {text[:80]}")
        print("DECISION:", (reply or "SILENCE")[:400])
        if reply and not dry:
            print(send_reply("test-mode-no-id", reply, dry=True))
        return
    for m in fetch_mentions():
        if m["id"] in seen or not m["id"]:
            continue
        seen.add(m["id"])
        reply = decide(m["text"], conn)
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
