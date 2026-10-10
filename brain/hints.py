"""Soft-shill lane: the poster never asked, so nothing is claimed.

A low-key bullish mention ($TICKER, no CA, no tag) resolves through
DexScreener search + the derivation crown. One clear pool or nothing —
multiple matches and empty results both refuse. A filed hint is
kind='hinted': a proposed CA, de-emphasized, never a position claim.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TICKER_RE = re.compile(r"\$([A-Za-z0-9]{2,12})\b")
BULL_RE = re.compile(
    r"\b(loading|accumulat|watching|eyeing|sleeping on|early|gem|"
    r"moon|runner|about to|heating|cooking|printing)\b", re.I)
CA_RE = re.compile(r"(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})")


def is_hint(text: str) -> str | None:
    """Bullish ticker talk with no CA and no tag. Returns ticker or None."""
    t = text or ""
    if CA_RE.search(t) or "track this" in t.lower():
        return None
    m = TICKER_RE.search(t)
    if not m or not BULL_RE.search(t):
        return None
    return m.group(1).upper()


def search_pools(ticker: str) -> list:
    """DexScreener symbol search, our chains only."""
    from watcher.common import CHAIN_SLUGS
    import httpx, time
    try:
        r = httpx.get("https://api.dexscreener.com/latest/dex/search",
                      params={"q": ticker}, timeout=20)
        out = []
        for p in (r.json().get("pairs") or []):
            base = p.get("baseToken") or {}
            if base.get("symbol", "").upper() != ticker.upper():
                continue
            chain = ("robinhood" if p.get("chainId") in ("robinhood", "4663")
                     else "solana" if p.get("chainId") in ("solana",) else "")
            if not chain:
                continue
            vol = p.get("volume") or {}
            tx = p.get("txns") or {}
            out.append({
                "mint": base.get("address", ""),
                "chain": chain, "symbol": base.get("symbol") or ticker,
                "liq": float((p.get("liquidity") or {}).get("usd") or 0),
                "vol_h24": float(vol.get("h24") or 0),
                "txns_h24": sum((v.get("buys", 0) + v.get("sells", 0))
                                for v in tx.values()
                                if isinstance(v, dict)),
                "age_min": 60})
        return out
    except Exception:
        return []


def resolve(ticker: str, pools: list | None = None) -> dict | None:
    """One clear pool or nothing. Crown refuses ties and thin traction."""
    from brain.derive import crown
    pools = search_pools(ticker) if pools is None else pools
    if not pools:
        return None
    r = crown(pools, keywords=[ticker])
    return r["leader"]


HINT_TEMPLATES = [
    "@{poster} hinted at ${ticker} — proposed {mint}, watching. not a call.",
    "soft signal from @{poster}: ${ticker} on the radar ({mint}). proposed only.",
]


def file_hinted(conn, poster: str, ticker: str, lead: dict,
                post_id: str = "") -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM callers WHERE handle = %s",
                    (poster.lower(),))
        row = cur.fetchone()
        if row:
            caller_id = row[0]
        else:
            cur.execute("INSERT INTO callers (handle) VALUES (%s) "
                        "RETURNING id", (poster.lower(),))
            caller_id = cur.fetchone()[0]
        url = f"https://x.com/i/status/{post_id or 'hint-' + lead['mint'][:16]}"
        cur.execute(
            """INSERT INTO calls (caller_id, coin, mint, chain,
                                  price_at_call, mcap_at_call,
                                  post_url, post_id, kind)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'hinted')
               ON CONFLICT (post_id) DO NOTHING""",
            (caller_id, lead.get("symbol") or ticker, lead["mint"],
             lead["chain"], None, None, url,
             post_id or f"hint-{lead['mint'][:16]}"))
        conn.commit()
    short = lead["mint"][:6] + "…" + lead["mint"][-4:]
    tpl = HINT_TEMPLATES[hash(ticker) % len(HINT_TEMPLATES)]
    return {"ticker": ticker, "mint": lead["mint"],
            "text": tpl.format(poster=poster, ticker=ticker,
                               mint=short)[:280]}
