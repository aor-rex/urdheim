"""Backdated entry pricing: what was it worth when the call was posted.

Solana: GeckoTerminal OHLCV candles (free, no key).
Robinhood: onchain Sync logs off the public RPC (proven 7d+ retention).
history_price(mint, chain, ts) -> {price, mcap, symbol, estimated} | None.
Never guesses: below confidence -> None, caller falls back to live.
"""
import time

import httpx

from watcher.common import ROBIN_RPC

SYNC_TOPIC = ("0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1")
STABLES = ("USDG", "USDC", "USDT", "DAI", "USDC.E", "USDT0", "WUSD")


def history_price(mint: str, chain: str, ts: float,
                    patient: bool = False) -> dict | None:
    """Entry snapshot at unix ts. None when history can't be read.

    patient=True retries GeckoTerminal past 429s (snitch context, not the
    reply path — GT rate-limits datacenter IPs)."""
    try:
        if chain == "solana":
            return _sol_history(mint, ts, patient)
        if chain == "robinhood":
            return _robin_history(mint, ts)
    except Exception:
        pass
    return None


# ---- solana: GeckoTerminal candles --------------------------------------
def _gt_get(url: str, patient: bool) -> httpx.Response | None:
    for attempt in range(3 if patient else 1):
        try:
            r = httpx.get(url, headers={"Accept": "application/json"},
                          timeout=20)
        except Exception:
            return None
        if r.status_code != 429 or not patient:
            return r
        time.sleep(65)
    return None


def _sol_history(mint: str, ts: float, patient: bool = False) -> dict | None:
    age = time.time() - ts
    if age < 0:
        return None
    r = _gt_get(
        f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}",
        patient)
    if r is None or r.status_code != 200:
        return None
    body = r.json()
    data = body.get("data") or {}
    pools = ((data.get("relationships") or {}).get("top_pools")
             or {}).get("data") or []
    if not pools:
        return None
    pool = pools[0].get("id", "").split("_", 1)[-1]
    now_price = float((data.get("attributes") or {}).get("price_usd") or 0)
    now_fdv = float((data.get("attributes") or {}).get("fdv_usd") or 0)
    if age < 20 * 3600:
        tf, dur, before, limit = "minute", 60, int(ts) + 300, min(int(age // 60) + 5, 1000)
    else:
        tf, dur, before, limit = "hour", 3600, int(ts) + 3600, min(int(age // 3600) + 5, 1000)
    r = _gt_get(
        f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}"
        f"/ohlcv/{tf}?before_timestamp={before}&limit={limit}",
        patient)
    if r is None or r.status_code != 200:
        return None
    rows = ((r.json().get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    hit = None
    for row in rows:
        if row[0] <= int(ts) < row[0] + dur:
            hit = row
            break
    if not hit:
        return None
    price = float(hit[4])
    if not price:
        return None
    mcap = price / now_price * now_fdv if now_price and now_fdv else 0
    return {"price": price, "mcap": mcap,
            "symbol": (data.get("attributes") or {}).get("symbol") or "",
            "estimated": True}


# ---- robinhood: Sync logs off the public RPC -----------------------------
def _rpc(method: str, params: list) -> dict:
    r = httpx.post(ROBIN_RPC, json={"jsonrpc": "2.0", "id": 1,
                                    "method": method, "params": params},
                   timeout=25)
    return r.json()


def _call(to: str, data: str, block: str = "latest") -> str:
    return (_rpc("eth_call", [{"to": to, "data": data}, block]).get("result") or "")


def _robin_history(mint: str, ts: float) -> dict | None:
    age = time.time() - ts
    if age < 0:
        return None
    r = httpx.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
                  timeout=20)
    pairs = [p for p in (r.json().get("pairs") or [])
             if p.get("chainId") == "robinhood"]
    if not pairs:
        return None
    pairs.sort(key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0),
               reverse=True)
    top = pairs[0]
    pair = top.get("pairAddress", "")
    if len(pair) != 42:
        return None
    quote = (top.get("quoteToken") or {})
    late = _rpc("eth_blockNumber", []).get("result", "")
    latest = int(late, 16)
    blk_ts = int(_rpc("eth_getBlockByNumber", [hex(latest), False])
                 .get("result", {}).get("timestamp", "0x0"), 16)
    step = 200000
    best, best_ts, first, first_ts = None, 0, None, 0
    seen_blocks: dict[int, int] = {}

    def block_ts(bn: int) -> int:
        if bn not in seen_blocks:
            b = _rpc("eth_getBlockByNumber", [hex(bn), False]).get("result") or {}
            seen_blocks[bn] = int(b.get("timestamp", "0x0"), 16)
        return seen_blocks[bn]

    hi = latest
    for _ in range(60):
        lo = max(hi - step, 0)
        logs = _rpc("eth_getLogs", [{"address": pair, "topics": [SYNC_TOPIC],
                                     "fromBlock": hex(lo),
                                     "toBlock": hex(hi)}]).get("result") or []
        for lg in logs:
            bn = int(lg.get("blockNumber", "0x0"), 16)
            t = block_ts(bn)
            if not first or t < first_ts:
                first, first_ts = lg, t
            if t <= ts and t > best_ts:
                best, best_ts = lg, t
        if best and best_ts >= ts - 3600:
            break
        if lo == 0:
            break
        hi = lo - 1
    pick, estimated = (best, True) if best else (first, True)
    if not pick:
        return None
    raw = (pick.get("data") or "0x")[2:]
    r0, r1 = int(raw[0:64], 16), int(raw[64:128], 16)
    t0 = ("0x" + (_call(pair, "0x0dfe1681") or "")[-40:]).lower()
    is_t0 = t0 == mint.lower()
    b_res = r0 if is_t0 else r1
    q_res = r1 if is_t0 else r0
    b_dec = int(_call(mint, "0x313ce567") or "0x0", 16) or 18
    q_dec = int(_call(quote.get("address", ""), "0x313ce567") or "0x0", 16) or 18
    if not b_res or not q_res:
        return None
    price_q = (q_res / 10 ** q_dec) / (b_res / 10 ** b_dec)
    qsym = (quote.get("symbol") or "").upper()
    if qsym in STABLES:
        q_usd, estimated = 1.0, False if best else True
    else:
        try:
            qr = httpx.get("https://api.dexscreener.com/latest/dex/tokens/"
                           + quote.get("address", ""), timeout=20)
            qp = [p for p in (qr.json().get("pairs") or [])
                  if p.get("chainId") == "robinhood"]
            q_usd = float((qp[0].get("priceUsd") if qp else 0) or 0)
        except Exception:
            q_usd = 0
        estimated = True
    if not q_usd:
        return None
    price = price_q * q_usd
    supply = int(_call(mint, "0x18160ddd") or "0x0", 16) / 10 ** b_dec
    return {"price": price, "mcap": price * supply if supply else 0,
            "symbol": (top.get("baseToken") or {}).get("symbol") or "",
            "estimated": estimated}
