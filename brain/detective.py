"""Call detective: API agent. Reads queued candidates, returns
call | soft-shill | chatting + confidence + evidence quote.
Key + model from .env. No CLI, no login."""
import json
import os

import httpx

API_BASE = os.environ.get("OPENCODE_API_BASE", "https://api.opencode.ai/v1")
PROMPT = """You review Solana memecoin X posts. Decide if the post is a CALL:
- "call": explicitly shilling a coin (CA posted, buy language, entry talk)
- "soft-shill": implies interest, denies intent ("not saying buy, just observing")
- "chatting": merely discussing, no shill
Reply ONLY as JSON: {"verdict": "...", "confidence": 0.0-1.0, "evidence": "short quote"}
Post by {author}: {text}"""


def classify(author: str, text: str) -> dict:
    key = os.environ.get("OPENCODE_API_KEY", "")
    model = os.environ.get("DETECT_MODEL", "")
    if not key or not model:
        raise SystemExit("set OPENCODE_API_KEY and DETECT_MODEL")
    r = httpx.post(
        API_BASE + "/chat/completions",
        headers={"Authorization": "Bearer " + key},
        json={
            "model": model,
            "messages": [{"role": "user", "content": PROMPT.format(
                author=author, text=text)}],
            "temperature": 0,
        },
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    return json.loads(content)


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
            # TODO: write verdicts to `calls` table


if __name__ == "__main__":
    main()
