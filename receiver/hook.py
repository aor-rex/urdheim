"""Urdheim webhook receiver: GetXAPI monitor deliveries land here.

POST /hook — verify HMAC, extract tweet, run the shared pipeline
(regex -> DexScreener snapshot -> queue.jsonl). Same queue format as the
twitterapi stream, so the detective can't tell transports apart.

Run: uvicorn receiver.hook:app --port 8091 (behind Dokploy + HTTPS).
Env: GETXAPI_WEBHOOK_SECRET (shown once at webhook creation), QUEUE_PATH.
"""
import hashlib
import hmac
import os

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from watcher.common import is_candidate, queue_candidate

app = FastAPI()


def verify(raw: bytes, signature: str) -> bool:
    secret = os.environ.get("GETXAPI_WEBHOOK_SECRET", "").encode()
    if not secret:
        return False
    digest = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    sig = signature.removeprefix("sha256=")
    return hmac.compare_digest(digest, sig)


def extract_tweet(payload: dict) -> tuple[str, str, str]:
    """Return (author, post_id, text) from a monitor delivery payload."""
    tw = payload.get("tweet") or payload.get("data") or payload
    author = ((tw.get("author") or {}).get("userName")
              or tw.get("screen_name") or payload.get("userName", "?"))
    post_id = str(tw.get("id") or tw.get("id_str") or "")
    text = tw.get("text") or tw.get("full_text") or ""
    return author, post_id, text


def handle_delivery(payload: dict, queue_path: str) -> int:
    author, post_id, text = extract_tweet(payload)
    if not text or not is_candidate(text):
        return 0
    return queue_candidate(queue_path, author, post_id, text)


@app.post("/hook")
async def hook(request: Request, x_signature: str = Header(default="")):
    raw = await request.body()
    if not verify(raw, x_signature):
        return JSONResponse({"ok": False}, status_code=401)
    import json

    n = handle_delivery(json.loads(raw),
                        os.environ.get("QUEUE_PATH", "/tmp/q.jsonl"))
    return {"ok": True, "queued": n}


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
