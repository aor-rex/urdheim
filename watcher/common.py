"""Shared Urdheim read-path helpers: CA/call-word regex, DexScreener
snapshot, queue writer. Used by the twitterapi stream AND the GetXAPI
webhook receiver — one pipeline, two transports."""
import json
import re

import httpx

BASE58 = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
CA_RE = re.compile(BASE58)
CALL_WORDS = re.compile(
    r"\b(buy|call|entry|entries|gem|moon|send it|last chance|ape|pump|100x)\b",
    re.I,
)


def find_cas(text: str) -> list[str]:
    return list(dict.fromkeys(CA_RE.findall(text or "")))


def is_candidate(text: str) -> bool:
    return bool(CA_RE.search(text or "") or CALL_WORDS.search(text or ""))


def snapshot_price(mint: str) -> dict | None:
    try:
        r = httpx.get(
            "https://api.dexscreener.com/latest/dex/tokens/" + mint, timeout=20
        )
        pairs = r.json().get("pairs") or []
        if not pairs:
            return None
        p = pairs[0]
        return {
            "price": float(p.get("priceUsd") or 0),
            "mcap": float(p.get("fdv") or p.get("marketCap") or 0),
            "liq": float((p.get("liquidity") or {}).get("usd") or 0),
        }
    except Exception:
        return None


def queue_candidate(queue_path: str, author: str, post_id: str, text: str) -> int:
    n = 0
    with open(queue_path, "a") as q:
        for mint in find_cas(text):
            q.write(json.dumps({
                "post_id": post_id,
                "author": author,
                "text": text[:500],
                "mint": mint,
                "snapshot": snapshot_price(mint),
            }) + "\n")
            n += 1
    return n
