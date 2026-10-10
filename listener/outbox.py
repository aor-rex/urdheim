"""Outbox: every write to X goes through here. Nothing else posts.

Three verbs: reply (ask-confirm, receipts), quote (milestones),
post (weekly board). All dry-run by default — live requires dry=False
AND an explicit allow flag so tests can never tweet.

Budget: free uny-x path first, every send appended to spend.jsonl.
Daily cap 25 sends; over cap raises instead of tweeting.
"""
from __future__ import annotations

import datetime
import json
import os

DAY_CAP = 25
SPEND = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "watcher", "spend.jsonl")


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _sent_today() -> int:
    n = 0
    try:
        with open(SPEND) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("day", d.get("ts", "")[:10]) == _today() \
                        and str(d.get("endpoint", "")).startswith("outbox/"):
                    n += 1
    except FileNotFoundError:
        pass
    return n


def _log(endpoint: str, cost: float = 0.0) -> None:
    d = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "day": _today(), "endpoint": endpoint, "cost": cost}
    with open(SPEND, "a") as f:
        f.write(json.dumps(d) + "\n")


def _check(text: str, dry: bool, allow_live: bool) -> dict | None:
    if len(text) > 280:
        raise ValueError(f"outbox: {len(text)} chars, over 280")
    if not text.strip():
        raise ValueError("outbox: empty text")
    if dry or not allow_live:
        return {"dry": True, "chars": len(text),
                "live": False, "reason": "dry-run" if dry else "no-allow"}
    if _sent_today() >= DAY_CAP:
        raise RuntimeError(f"outbox: day cap {DAY_CAP} hit, refusing")
    return None


def _client():
    from unyx import UnyxClient
    path = os.environ.get("LISTENER_COOKIES", "")
    if not path:
        raise RuntimeError("outbox: no cookies — set LISTENER_COOKIES")
    c = UnyxClient()
    if not c.login_from_cookies(path):
        raise RuntimeError("outbox: cookie login failed")
    return c


def reply(post_id: str, text: str, dry: bool = True,
          allow_live: bool = False) -> dict:
    skip = _check(text, dry, allow_live)
    if skip:
        return {"verb": "reply", **skip, "post_id": post_id}
    with _client() as c:
        out = c.reply(post_id, text)
    _log("outbox/reply")
    return {"verb": "reply", "live": True, "out": out}


def quote(post_id: str, text: str, dry: bool = True,
          allow_live: bool = False) -> dict:
    """Quote-tweet = post with the tweet URL appended (X auto-embeds)."""
    url = f"https://x.com/i/status/{post_id}"
    sep = "\n" if len(text) + 1 + len(url) <= 280 else " "
    return post(text + sep + url, dry=dry, allow_live=allow_live,
                verb="quote", post_id=post_id)


def post(text: str, dry: bool = True, allow_live: bool = False,
         verb: str = "post", post_id: str = "") -> dict:
    skip = _check(text, dry, allow_live)
    if skip:
        return {"verb": verb, **skip, "post_id": post_id}
    with _client() as c:
        out = c.post(text)
    _log(f"outbox/{verb}")
    return {"verb": verb, "live": True, "out": out}
