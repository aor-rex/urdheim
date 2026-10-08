"""Mention intent via the brain, not regex.

classify_mention(author, text) -> {intent, handle, mint, note}
  intent: receipt_coin | receipt_caller | track_caller | track_call | ignore
The model reads conversation; the listener only executes. Same Go endpoint
pattern as detective (session header, responses shape both supported).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.detective import API_BASE, API_PATH, SESSION  # noqa: E402

import httpx  # noqa: E402

PROMPT = """You route mentions to an X bot that tracks memecoin callers.
Read the mention and return ONE intent as JSON only:
{{"intent": "...", "handle": "...", "mint": "...", "note": "..."}}
Intents:
- "receipt_coin": wants price/calls on a coin (CA present or named coin)
- "receipt_caller": asks about a caller's record ("is X legit", "X's calls")
- "track_caller": wants a caller tracked going forward ("track X", "watch X")
- "track_call": wants THIS specific call logged ("track this", quoted call + request)
- "ignore": chatter, greetings, jokes, unclear — stay silent
handle = the X handle in question (no @), or "". mint = the contract
address if present, or "". note = <10 words why.
Mention by {author}: {text}"""


def classify_mention(author: str, text: str) -> dict:
    import brain.detective as det
    from brain.budget import allow, log, BudgetStop

    key = os.environ.get("OPENCODE_API_KEY", "")
    model = os.environ.get("DETECT_MODEL", "")
    if not key or not model:
        raise RuntimeError("set OPENCODE_API_KEY and DETECT_MODEL")
    ok, reason = allow("model/intent")
    if not ok:
        raise BudgetStop(f"budget stop: {reason}")
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
    log("model/intent")
    body = r.json()
    if "choices" in body:
        content = body["choices"][0]["message"]["content"]
    else:
        chunks = []
        for item in body.get("output", []):
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    chunks.append(part.get("text", ""))
        content = "".join(chunks)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0]
    out = json.loads(content)
    if out.get("intent") not in ("receipt_coin", "receipt_caller",
                                 "track_caller", "track_call", "ignore"):
        out["intent"] = "ignore"
    return {"intent": out.get("intent", "ignore"),
            "handle": (out.get("handle") or "").lstrip("@"),
            "mint": out.get("mint") or "",
            "note": out.get("note") or ""}
