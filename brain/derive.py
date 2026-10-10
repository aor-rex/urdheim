"""Derivation scorer: one viral meme spawns five coins claiming to be
"the" one. Numbers crown the winner — not who shouted first.

Match stack, cheapest first:
  1. ticker text vs meme keywords (free, pure)
  2. image dHash: viral image vs token art (PIL, no model)
  3. vision describe: EXTENSION POINT — no model wired yet, returns None
  4. crowd pick: confirmation only, breaks near-ties, never decides alone

Refuse when thin: no leader without margin AND minimum traction.
A wrong CA under the brand is the one unrecoverable error.
"""
import io
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

MIN_LIQ = float(os.environ.get("DERIVE_MIN_LIQ", "5000"))
MIN_VOL = float(os.environ.get("DERIVE_MIN_VOL", "10000"))
MARGIN = 1.5  # leader must outscore runner-up by this much


def fetch_stats(mint: str, chain: str) -> dict | None:
    """DexScreener pair facts for one mint. None when no pair exists."""
    from watcher.common import CHAIN_SLUGS
    import httpx
    slugs = CHAIN_SLUGS.get(chain, ())
    try:
        r = httpx.get("https://api.dexscreener.com/latest/dex/tokens/" + mint,
                      timeout=20)
        pairs = [p for p in (r.json().get("pairs") or [])
                 if p.get("chainId") in slugs]
        if not pairs:
            return None
        p = max(pairs,
                key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
        vol = p.get("volume") or {}
        tx = p.get("txns") or {}
        txns = sum((v.get("buys", 0) + v.get("sells", 0))
                   for v in tx.values() if isinstance(v, dict))
        base = p.get("baseToken") or {}
        info = p.get("info") or {}
        created = p.get("pairCreatedAt", 0) or 0
        import time
        return {"mint": mint, "chain": chain,
                "symbol": base.get("symbol") or "",
                "liq": float((p.get("liquidity") or {}).get("usd") or 0),
                "vol_h24": float(vol.get("h24") or 0),
                "txns_h24": txns,
                "age_min": max(0, (time.time() * 1000 - created) / 60000)
                if created else 0,
                "image": info.get("imageUrl") or ""}
    except Exception:
        return None


def score(s: dict) -> float:
    """Log-scale chain facts. Pure — the committee is a calculator."""
    return (math.log10(1 + s.get("liq", 0)) * 0.4
            + math.log10(1 + s.get("vol_h24", 0)) * 0.3
            + math.log10(1 + s.get("txns_h24", 0)) * 0.2
            + math.log10(1 + s.get("age_min", 0)) * 0.1)


def name_score(symbol: str, keywords: list) -> float:
    """Token overlap between ticker and meme keywords. 0..1."""
    sym = (symbol or "").lower()
    if not sym or not keywords:
        return 0.0
    hit = sum(1 for k in keywords if k.lower() in sym or sym in k.lower())
    return hit / max(1, len(keywords))


def dhash(png: bytes) -> int:
    """Difference hash, 64-bit. Near-duplicate images, milliseconds."""
    from PIL import Image
    img = Image.open(io.BytesIO(png)).convert("L").resize((9, 8))
    px = list(img.getdata())
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | (
                1 if px[y * 9 + x] > px[y * 9 + x + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def describe_image(png: bytes) -> None:
    """Vision fallback. No model wired yet — returns None, never guesses."""
    return None


def crown(stats: list, keywords: list | None = None,
          crowd_pick: str = "",
          image_dist: dict | None = None) -> dict:
    """Pick the leading CA or refuse. Returns {leader|None, contenders}."""
    keywords = keywords or []
    image_dist = image_dist or {}
    if not stats:
        return {"leader": None, "contenders": [], "reason": "no candidates"}
    ranked = []
    for s in stats:
        total = score(s) + name_score(s.get("symbol", ""), keywords) * 0.5
        if s.get("mint") in image_dist:
            total += max(0, (16 - image_dist[s["mint"]]) / 16) * 0.5
        ranked.append((total, s))
    ranked.sort(key=lambda r: -r[0])
    best, rest = ranked[0], ranked[1:]
    s = best[1]
    traction = s.get("liq", 0) >= MIN_LIQ or s.get("vol_h24", 0) >= MIN_VOL
    margin = (best[0] / rest[0][0]) if rest and rest[0][0] > 0 else 9.9
    if rest and crowd_pick and rest[0][1].get("mint") == crowd_pick \
            and margin < MARGIN:
        return {"leader": None, "contenders": [r[1] for r in ranked],
                "reason": "crowd disagrees, holding contenders"}
    if not traction:
        return {"leader": None, "contenders": [r[1] for r in ranked],
                "reason": "thin: no traction yet"}
    if rest and margin < MARGIN:
        if best[1].get("mint") == crowd_pick:
            return {"leader": best[1],
                    "contenders": [r[1] for r in rest],
                    "reason": "crowd-confirmed"}
        return {"leader": None, "contenders": [r[1] for r in ranked],
                "reason": "thin: no margin"}
    return {"leader": s, "contenders": [r[1] for r in rest], "reason": "ok"}


def file_proposed(conn, mint: str, chain: str, note: str = "") -> int | None:
    """Leader without confirmation -> intake queue as proposed, never a call."""
    url = f"https://x.com/i/status/derive-{mint[:16]}"
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM submissions WHERE post_url = %s", (url,))
        if cur.fetchone():
            return None
        cur.execute(
            """INSERT INTO submissions (post_url, suggested_caller,
                                        reporter_ip, status)
               VALUES (%s, %s, 'derive', 'pending') RETURNING id""",
            (url, f"derive:{mint}" + (f" {note}" if note else "")))
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
