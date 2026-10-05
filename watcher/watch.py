"""Urdheim stream watcher: twitterapi.io WebSocket filter stream over tracked
callers -> CA/call-word regex -> DexScreener snapshot -> queue for detective.

Read path needs no cookies, no shells, no polling. One API key, sub-second.
"""
import asyncio
import json
import os
import re

import httpx

API = "https://api.twitterapi.io"
WS = "wss://ws.twitterapi.io/twitter/tweet/stream"

BASE58 = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
CA_RE = re.compile(BASE58)
CALL_WORDS = re.compile(
    r"\b(buy|call|entry|entries|gem|moon|send it|last chance|ape|pump|100x)\b",
    re.I,
)

CHUNK = 40  # handles per filter rule (tune live against rule length limits)


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


def headers() -> dict:
    return {"X-API-Key": os.environ["TWITTERAPI_KEY"]}


def chunk_rules(handles: list[str]) -> list[str]:
    rules = []
    for i in range(0, len(handles), CHUNK):
        group = handles[i : i + CHUNK]
        rules.append(" OR ".join(f"from:{h}" for h in group))
    return rules


def set_rules(rules: list[str]) -> None:
    # replace existing rules, then add ours (adjust to actual rule API)
    httpx.post(f"{API}/oapi/tweet_filter/add_rule",
               headers=headers(), json={"rules": rules}, timeout=30).raise_for_status()
    print(f"rules set: {len(rules)}", flush=True)


def backfill(handle: str, since_id: str = "") -> list[dict]:
    """Pull recent posts for a caller (onboarding + gap recovery)."""
    params: dict = {"query": f"from:{handle}", "queryType": "Latest"}
    if since_id:
        params["sinceId"] = since_id
    r = httpx.get(f"{API}/twitter/tweet/advanced_search",
                  headers=headers(), params=params, timeout=30)
    return (r.json().get("tweets") or [])


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


async def stream_loop(queue_path: str) -> None:
    import websockets  # pip: websockets

    backoff = 5
    while True:
        try:
            async with websockets.connect(WS, extra_headers=headers()) as ws:
                print("stream connected", flush=True)
                backoff = 5
                async for raw in ws:
                    try:
                        tweet = json.loads(raw)
                    except Exception:
                        continue
                    text = tweet.get("text") or tweet.get("full_text") or ""
                    if not is_candidate(text):
                        continue
                    author = ((tweet.get("author") or {}).get("userName")
                              or tweet.get("screen_name") or "?")
                    n = queue_candidate(queue_path,
                                        author, str(tweet.get("id")), text)
                    if n:
                        print(f"queued {n} from @{author}", flush=True)
        except Exception as e:
            print(f"stream dropped ({e}), retry in {backoff}s", flush=True)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 300)


def main():
    seed_path = os.environ.get("SEED_PATH", "watcher/seed.json")
    with open(seed_path) as f:
        seed = json.load(f)  # [{"handle": "..."}, ...]
    handles = [s["handle"].lstrip("@") for s in seed]
    queue_path = os.environ.get("QUEUE_PATH", "watcher/queue.jsonl")
    set_rules(chunk_rules(handles))
    # backlog for every caller on boot (cheap: ~20 tweets each)
    for h in handles:
        for t in backfill(h):
            text = t.get("text") or ""
            if is_candidate(text):
                queue_candidate(queue_path, h, str(t.get("id")), text)
    print(f"streaming {len(handles)} callers, queue -> {queue_path}", flush=True)
    asyncio.run(stream_loop(queue_path))


if __name__ == "__main__":
    main()
