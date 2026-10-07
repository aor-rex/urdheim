"""Shared Urdheim read-path helpers: CA/call-word regex, price
snapshot, queue writer. Used by the twitterapi stream AND the GetXAPI
webhook receiver — one pipeline, two transports.

Price sources, in order: DexScreener, then GeckoTerminal (solana) or
direct pool reads off the Robinhood public RPC (no key, no block)."""
import json
import re

import httpx

BASE58 = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
CA_RE = re.compile(BASE58)
EVM_RE = re.compile(r"0x[0-9a-fA-F]{40}")

# DexScreener chain slugs per Urdheim chain. Solana pairs come back as
# chainId "solana"; Robinhood Chain as "robinhood".
CHAIN_SLUGS = {"solana": ("solana",), "robinhood": ("robinhood",)}

# Robinhood Chain (4663) onchain reads: public RPC + the chain's v2
# factory (found via pair factory(), canonical 0x5C69... not deployed).
# Beats every aggregator block: RPC serves this box fine.
ROBIN_RPC = "https://rpc.mainnet.chain.robinhood.com"
ROBIN_V2_FACTORY = "0x8bCeAa40b9acdfaedf85adf4ff01f5ad6517937F"
ROBIN_WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
MAINNET_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
_ETH_USD = 0.0


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
    if chain == "robinhood":
        return _evm_snapshot(mint)
    return None


def _eth_usd() -> float:
    """ETH price, cached per process. Coinbase first, Kraken backup,
    GeckoTerminal last (it rate-limits datacenter IPs)."""
    global _ETH_USD
    if _ETH_USD:
        return _ETH_USD
    try:
        r = httpx.get("https://api.coinbase.com/v2/prices/ETH-USD/spot",
                      timeout=20)
        _ETH_USD = float((r.json().get("data") or {}).get("amount") or 0)
    except Exception:
        pass
    if not _ETH_USD:
        try:
            r = httpx.get("https://api.kraken.com/0/public/Ticker",
                          params={"pair": "ETHUSD"}, timeout=20)
            _ETH_USD = float(((r.json().get("result") or {})
                              .get("XETHZUSD", {}).get("c") or [0])[0])
        except Exception:
            pass
    if not _ETH_USD:
        try:
            r = httpx.get(
                "https://api.geckoterminal.com/api/v2/networks/ethereum/tokens/"
                + MAINNET_WETH,
                headers={"Accept": "application/json"}, timeout=20)
            a = (r.json().get("data") or {}).get("attributes") or {}
            _ETH_USD = float(a.get("price_usd") or 0)
        except Exception:
            pass
    return _ETH_USD


def _rpc(method: str, params: list) -> dict:
    r = httpx.post(ROBIN_RPC, json={"jsonrpc": "2.0", "id": 1,
                                    "method": method, "params": params},
                   timeout=25)
    return r.json()


def _evm_snapshot(mint: str) -> dict | None:
    """Robinhood v2 pool read: getPair -> getReserves/token0/decimals.
    Price in WETH x ETH-USD; liq = 2x WETH side (standard v2 math)."""
    def enc(a: str) -> str:
        return "0" * 24 + a[2:].lower()

    try:
        pair = _rpc("eth_call", [{
            "to": ROBIN_V2_FACTORY,
            "data": "0xe6a43905" + enc(mint) + enc(ROBIN_WETH)}, "latest"])
        pair_addr = "0x" + (pair.get("result") or "")[-40:]
        if int(pair_addr, 16) == 0:
            return None
        res = _rpc("eth_call", [{"to": pair_addr,
                                 "data": "0x0902f1ac"}, "latest"])
        t0 = _rpc("eth_call", [{"to": pair_addr,
                                "data": "0x0dfe1681"}, "latest"])
        dec = _rpc("eth_call", [{"to": mint, "data": "0x313ce567"},
                                "latest"])
        raw = (res.get("result") or "")[2:]
        r0, r1 = int(raw[0:64], 16), int(raw[64:128], 16)
        is_t0 = ("0x" + (t0.get("result") or "")[-40:]).lower() == mint.lower()
        tok_res = r0 if is_t0 else r1
        weth_res = r1 if is_t0 else r0
        tdec = int((dec.get("result") or "0"), 16) or 18
        eth = _eth_usd()
        if not tok_res or not eth:
            return None
        price_weth = (weth_res / 1e18) / (tok_res / 10 ** tdec)
        liq = 2 * (weth_res / 1e18) * eth
        return {"chain": "robinhood", "symbol": "", "price": price_weth * eth,
                "mcap": 0, "liq": liq}
    except Exception:
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
