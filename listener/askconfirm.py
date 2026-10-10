"""Ask-confirm: the asker gets the receipt, not the poster.

A mention that is basically just "ca?" under a popping post files an
INTEREST ask (snapshot priced now, from chain). The account replies
asking "did you get in?" — a yes files a CONFIRMED receipt with the
ask-time price, silence leaves the interest receipt standing alone.
No response is never read as a position.

Gates: parent post must clear ASK_MIN_LIKES (default 100) or involve
a tracked caller, or the account would look like a reply-bot.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

CA_ASK_RE = re.compile(
    r"^\s*(cas*\??|contracts*\??|address(es)?\??|addy\??|"
    r"drop( the)? (ca|contract|addy)\??|ca pls\??|need (that|the) ca\??)\s*$",
    re.I)
YES_RE = re.compile(
    r"\b(got ?in|aped?|bought|copped|grabbed|filled|im in|i'm in|"
    r"secured|loaded|yes+|yeah+yup)\b", re.I)

ASK_MIN_LIKES = int(os.environ.get("ASK_MIN_LIKES", "100"))
ASK_TTL_DAYS = 7

ASK_TEMPLATES = [
    "want a receipt @{asker}? reply got in and i'll file it.",
    "@{asker} hunting. you get in? say the word, receipt's yours.",
    "noted @{asker} — did you catch it? confirm and it's on the ledger.",
]


def is_ca_ask(text: str) -> bool:
    return bool(CA_ASK_RE.match(text or ""))


def is_yes(text: str) -> bool:
    return bool(YES_RE.search(text or ""))


def ask_text(asker: str, ask_id: int) -> str:
    return ASK_TEMPLATES[ask_id % len(ASK_TEMPLATES)].format(asker=asker)


def pending(conn, asker: str):
    """Newest open ask for this handle, or None."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, mint, chain, price_at_ask, mcap_at_ask
               FROM asks WHERE asker = %s AND status = 'asked'
               ORDER BY asked_at DESC LIMIT 1""", (asker.lower(),))
        r = cur.fetchone()
        return {"id": r[0], "mint": r[1], "chain": r[2],
                "price": r[3], "mcap": r[4]} if r else None


def handle_ask(conn, asker: str, ask_post_id: str, mint: str,
               parent_post_id: str = "") -> dict:
    """File interest, snapshot ask-time price from chain. Idempotent."""
    from watcher.common import snapshot_price, detect_chain
    chain = detect_chain(mint)
    try:
        snap = snapshot_price(mint, chain) or {}
    except Exception:
        snap = {}
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO asks (asker, mint, chain, ask_post_id,
                                 parent_post_id, price_at_ask, mcap_at_ask)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (asker, ask_post_id) DO NOTHING
               RETURNING id""",
            (asker.lower(), mint, chain, ask_post_id, parent_post_id,
             snap.get("price"), snap.get("mcap")))
        row = cur.fetchone()
        conn.commit()
        ask_id = row[0] if row else 0
    return {"ask_id": ask_id, "text": ask_text(asker, ask_id),
            "price": snap.get("price"), "mcap": snap.get("mcap")}


def handle_confirm(conn, asker: str, text: str) -> dict | None:
    """Yes -> confirmed receipt at the ASK-time chain price. Else None."""
    if not is_yes(text):
        return None
    ask = pending(conn, asker)
    if not ask:
        return None
    from watcher.common import snapshot_price
    try:
        snap = snapshot_price(ask["mint"], ask["chain"]) or {}
    except Exception:
        snap = {}
    symbol = snap.get("symbol") or ask["mint"][:8]
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM callers WHERE handle = %s",
                    (asker.lower(),))
        row = cur.fetchone()
        if row:
            caller_id = row[0]
        else:
            cur.execute(
                "INSERT INTO callers (handle) VALUES (%s) RETURNING id",
                (asker.lower(),))
            caller_id = cur.fetchone()[0]
        url = f"https://x.com/i/status/{ask['id']}-ask"
        cur.execute(
            """INSERT INTO calls (caller_id, coin, mint, chain,
                                  price_at_call, mcap_at_call,
                                  post_url, post_id, kind)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'asked')
               ON CONFLICT (post_id) DO NOTHING""",
            (caller_id, symbol, ask["mint"], ask["chain"],
             ask["price"], ask["mcap"], url, f"ask-{ask['id']}"))
        cur.execute("UPDATE asks SET status = 'confirmed' WHERE id = %s",
                    (ask["id"],))
        conn.commit()
    return {"ask_id": ask["id"], "coin": symbol,
            "text": (f"filed @{asker} — ${symbol} receipt at the ask price. "
                     f"ledger has it.")[:280]}


def expire(conn) -> int:
    """Silence is never a position: old asks just lapse."""
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE asks SET status = 'expired'
               WHERE status = 'asked'
                 AND asked_at < now() - (%s || ' days')::interval""",
            (str(ASK_TTL_DAYS),))
        n = cur.rowcount
        conn.commit()
        return n


def main() -> None:
    import psycopg
    with psycopg.connect(os.environ["DB_URL"]) as conn:
        print(f"expire: {expire(conn)} lapsed", flush=True)


if __name__ == "__main__":
    main()
