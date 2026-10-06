"""Urdheim GetXAPI read path: monitor management + backfill/poll client.

Real-time arrives via HMAC-signed webhooks -> receiver/hook.py (same queue
format as the twitterapi stream). This module handles everything else:
registering callers as monitors, onboarding backfill, gap-recovery polling.

Pricing: monitor delivery is NOT per-call (needs a Monitoring plan — confirm
cost on the dashboard before enabling). user/tweets backfill/poll is
$0.001/call (~20 tweets).
"""
import os

import httpx

API = "https://api.getxapi.com"


def headers() -> dict:
    return {"Authorization": "Bearer " + os.environ["GETXAPI_KEY"]}


def add_monitor(handle: str, webhook_url: str, tier: str = "fast",
                include_replies: bool = False) -> dict:
    """Watch a caller. New tweets push to webhook_url within ~2s (fast)."""
    r = httpx.post(f"{API}/twitter/monitor/add", headers=headers(), json={
        "userName": handle.lstrip("@"),
        "webhook_url": webhook_url,
        "tier": tier,
        "include_replies": include_replies,
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def list_monitors() -> dict:
    r = httpx.get(f"{API}/twitter/monitor/list",
                  headers=headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def remove_monitor(handle: str) -> dict:
    r = httpx.post(f"{API}/twitter/monitor/remove", headers=headers(),
                   json={"userName": handle.lstrip("@")}, timeout=30)
    r.raise_for_status()
    return r.json()


def backfill(handle: str, cursor: str = "") -> tuple[list[dict], str]:
    """Recent tweets for onboarding a caller. Returns (tweets, next_cursor)."""
    params: dict = {"userName": handle.lstrip("@")}
    if cursor:
        params["cursor"] = cursor
    r = httpx.get(f"{API}/twitter/user/tweets", headers=headers(),
                  params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    tweets = data.get("tweets") or data.get("data", {}).get("tweets") or []
    return tweets, data.get("next_cursor") or data.get("cursor") or ""


def poll_since(handle: str, cursor_file: str) -> list[dict]:
    """Gap-recovery poll: fetch one page past the saved cursor, save new one."""
    cursor = ""
    if os.path.exists(cursor_file):
        with open(cursor_file) as f:
            cursor = f.read().strip()
    tweets, nxt = backfill(handle, cursor)
    if nxt and nxt != cursor:
        with open(cursor_file, "w") as f:
            f.write(nxt)
    return tweets
