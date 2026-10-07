"""Shared Urdheim read-path helpers: CA/call-word regex, DexScreener
snapshot, queue writer. Used by the twitterapi stream AND the GetXAPI
webhook receiver — one pipeline, two transports."""
import json
import re

import httpx

BASE58 = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
CA_RE = re.compile(BASE58)
EVM_RE = re.compile(r"0x[0-9a-fA-F]{40}")

# DexScreener chain slugs per Urdheim chain. Solana pairs come back as
# chainId "solana"; Robinhood Chain as "robinhood".
CHAIN_SLUGS = {"solana": ("solana",), "robinhood": ("robinhood",)}


def detect_chain(mint: str) -> str:
    """0x-address -> robinhood, base58 -> solana. Format decides, always."""
    if mint.startswith(("0x", "0X")):
        return "robinhood"
    return "solana"


def find_cas(text: str) -> list[str]:
    found = CA_RE.findall(text or "")
    found += EVM_RE.findall(text or "")
    return list(dict.fromkeys(found))
CALL_WORDS = re.compile(
    r"\b(buy|call|entry|entries|gem|moon|send it|last chance|ape|pump|100x)\b",
    re.I,
)


def is_candidate(text: str) -> bool:
    return bool(CA_RE.search(text or "") or EVM_RE.search(text or "")
                or CALL_WORDS.search(text or ""))


def snapshot_price(mint: str, chain: str | None = None) -> dict | None:
    """DexScreener snapshot, pairs filtered to the mint's chain.
    Same /tokens endpoint returns every chain — without the filter a
    0x address could snapshot the wrong chain's pair.
    Falls back to GeckoTerminal (solana only — robinhood chain isn't
    indexed there) when DexScreener serves empty, e.g. datacenter IP."""
    chain = chain or detect_chain(mint)
    slugs = CHAIN_SLUGS.get(chain, ())
    try:
        r = httpx.get(
            "https://api.dexscreener.com/latest/dex/tokens/" + mint, timeout=20
        )
        pairs = [p for p in (r.json().get("pairs") or [])
                 if p.get("chainId") in slugs]
        if pairs:
            p = pairs[0]
            base = p.get("baseToken") or {}
            return {
                "chain": chain,
                "symbol": base.get("symbol") or "",
                "price": float(p.get("priceUsd") or 0),
                "mcap": float(p.get("fdv") or p.get("marketCap") or 0),
                "liq": float((p.get("liquidity") or {}).get("usd") or 0),
            }
    except Exception:
        pass
    if chain == "solana":
        return _gt_snapshot(mint)
    return None


def _gt_snapshot(mint: str) -> dict | None:
    """GeckoTerminal token read: price + reserves in one free call."""
    try:
        r = httpx.get(
            f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}",
            headers={"Accept": "application/json"}, timeout=20)
        if r.status_code != 200:
            return None
        a = (r.json().get("data") or {}).get("attributes") or {}
        price = float(a.get("price_usd") or 0)
        if not price:
            return None
        return {
            "chain": "solana",
            "symbol": a.get("symbol") or "",
            "price": price,
            "mcap": float(a.get("fdv_usd") or a.get("market_cap_usd") or 0),
            "liq": float(a.get("total_reserve_in_usd") or 0),
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
                "chain": detect_chain(mint),
                "snapshot": snapshot_price(mint),
            }) + "\n")
            n += 1
    return n
