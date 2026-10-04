"""Urdheim watcher: poll tracked callers, regex for CAs + call language,
snapshot price on match, queue for the detective. Read-only, never posts."""
import json
import os
import re
import time

import httpx

BASE58 = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
CA_RE = re.compile(BASE58)
CALL_WORDS = re.compile(
    r"\b(buy|call|entry|entries|gem|moon|send it|last chance|ape|pump|100x)\b",
    re.I,
)

POLL = {1: 180, 2: 900, 3: 1800}  # seconds per tier


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


def main():
    seed_path = os.environ.get("SEED_PATH", "watcher/seed.json")
    with open(seed_path) as f:
        seed = json.load(f)  # [{"handle": "...", "tier": 1}, ...]
    out = os.environ.get("QUEUE_PATH", "watcher/queue.jsonl")
    print(f"watching {len(seed)} callers, queue -> {out}", flush=True)
    # NOTE: per-caller polling via uny-x plugs in here once WATCHER_COOKIES
    # is on the box. Until then this validates regex + price snapshots
    # against a timeline dump passed via TIMELINE_DUMP (jsonl of post dicts).
    dump = os.environ.get("TIMELINE_DUMP", "")
    if not dump:
        print("no TIMELINE_DUMP set — poll loop goes live with cookies.", flush=True)
        return
    queued = 0
    with open(dump) as f, open(out, "a") as q:
        for line in f:
            try:
                post = json.loads(line)
            except Exception:
                continue
            text = post.get("full_text") or post.get("text") or ""
            if not is_candidate(text):
                continue
            for mint in find_cas(text):
                snap = snapshot_price(mint)
                q.write(json.dumps({
                    "post_id": post.get("id_str"),
                    "author": post.get("author"),
                    "text": text[:500],
                    "mint": mint,
                    "snapshot": snap,
                }) + "\n")
                queued += 1
    print(f"queued {queued} candidates", flush=True)


if __name__ == "__main__":
    main()
