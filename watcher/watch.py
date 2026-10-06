"""Urdheim stream watcher: twitterapi.io WebSocket filter stream over tracked
callers -> CA/call-word regex -> DexScreener snapshot -> queue for detective.

Read path needs no cookies, no shells, no polling. One API key, sub-second.
"""
import asyncio
import json
import os
import re

import httpx

from common import is_candidate, queue_candidate

API = "https://api.twitterapi.io"
WS = os.environ.get("TWITTERAPI_WS", "wss://ws.twitterapi.io/twitter/tweet/stream")

CHUNK = 40  # handles per filter rule (tune live against rule length limits)


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


async def stream_loop(queue_path: str) -> None:
    import websockets  # pip: websockets

    backoff = 5
    import inspect
    _hdr = ("additional_headers"
            if "additional_headers" in inspect.signature(websockets.connect).parameters
            else "extra_headers")
    while True:
        try:
            async with websockets.connect(WS, **{_hdr: headers()}) as ws:
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
