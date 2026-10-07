"""Call detective: API agent. Reads queued candidates, returns
call | soft-shill | chatting + confidence + evidence quote.
Key + model from .env. No CLI, no login."""
import json
import os

import httpx

API_BASE = os.environ.get("OPENCODE_API_BASE", "https://api.opencode.ai/v1")
API_PATH = os.environ.get("OPENCODE_API_PATH", "/chat/completions")
SESSION = os.environ.get("OPENCODE_SESSION", "urdheim-brain")
PROMPT = """You review Solana memecoin X posts. Decide if the post is a CALL:
- "call": explicitly shilling a coin (CA posted, buy language, entry talk)
- "soft-shill": implies interest, denies intent ("not saying buy, just observing")
- "chatting": merely discussing, no shill
Reply ONLY as JSON: {{{{"verdict": "...", "confidence": 0.0-1.0, "evidence": "short quote"}}}}
Post by {author}: {text}"""


def classify(author: str, text: str) -> dict:
    key = os.environ.get("OPENCODE_API_KEY", "")
    model = os.environ.get("DETECT_MODEL", "")
    if not key or not model:
        raise SystemExit("set OPENCODE_API_KEY and DETECT_MODEL")
    r = httpx.post(
        API_BASE + API_PATH,
        headers={"Authorization": "Bearer " + key,
                 "x-opencode-session": SESSION,
                 "User-Agent": "urdheim/1.0"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": PROMPT.format(
                author=author, text=text)}],
            "temperature": 0,
        } if API_PATH.endswith("chat/completions") else {
            "model": model,
            "input": PROMPT.format(author=author, text=text),
        },
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    if "choices" in body:  # chat/completions shape
        content = body["choices"][0]["message"]["content"]
    else:  # responses shape: output[].content[].text
        chunks = []
        for item in body.get("output", []):
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    chunks.append(part.get("text", ""))
        content = "".join(chunks)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(content)


def record_call(item: dict, verdict: dict) -> None:
    """Write a detective verdict into `calls` (creating the caller row)."""
    import psycopg

    with psycopg.connect(os.environ["DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO callers(handle) VALUES (%s) "
            "ON CONFLICT (handle) DO NOTHING",
            (item.get("author", "?"),),
        )
        cur.execute("SELECT id FROM callers WHERE handle = %s",
                    (item.get("author", "?"),))
        caller_id = cur.fetchone()[0]
        snap = item.get("snapshot") or {}
        if not snap.get("price") and item.get("mint"):
            from watcher.common import snapshot_price
            snap = snapshot_price(item["mint"],
                                  item.get("chain")) or {}
        coin = (item.get("coin") not in (None, "?", "")
                and item["coin"]) or snap.get("symbol") or "?"
        cur.execute(
            """INSERT INTO calls(caller_id, coin, mint, chain, price_at_call,
                                 mcap_at_call, post_url, post_id, called_at,
                                 verdict, confidence, evidence_quote)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s, %s)
               ON CONFLICT (post_id) DO NOTHING""",
            (caller_id, coin, item.get("mint"),
             item.get("chain") or (snap.get("chain") or "solana"),
             snap.get("price"), snap.get("mcap"),
             f"https://x.com/i/status/{item.get('post_id')}",
             str(item.get("post_id")),
             verdict.get("verdict"), verdict.get("confidence"),
             verdict.get("evidence")),
        )
        conn.commit()


def main():
    queue = os.environ.get("QUEUE_PATH", "watcher/queue.jsonl")
    with open(queue) as f:
        for line in f:
            item = json.loads(line)
            try:
                v = classify(item.get("author", "?"), item.get("text", ""))
            except Exception as e:
                print("FAIL", item.get("post_id"), str(e)[:100], flush=True)
                continue
            print(json.dumps({"post_id": item.get("post_id"),
                              "mint": item.get("mint"), **v}), flush=True)
            if v.get("verdict") in ("call", "soft-shill") and v.get(
                    "confidence", 0) >= 0.7:
                record_call(item, v)


if __name__ == "__main__":
    main()
