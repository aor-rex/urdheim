"""Urdheim GetXAPI write path: Heimdall posting through one key.

POST /twitter/tweet/create takes auth_token (+ct0) per request — no
dashboard registration, no password. Cookies live in a file (same export
as uny-x), key in env. $0.002 per post.

Usage:
    GETXAPI_KEY=... poster/getxapi.py "text" [--cookies PATH] [--dry]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

from brain.budget import allow, log

API = "https://api.getxapi.com"


def load_tokens(path: str) -> tuple[str, str]:
    raw = json.load(open(path))
    items = raw if isinstance(raw, list) else raw.get("cookies", [])
    kv = {c.get("name"): c.get("value") for c in items}
    return kv.get("auth_token", ""), kv.get("ct0", "")


def post(text: str, cookies_path: str, dry: bool = False) -> dict:
    auth_token, ct0 = load_tokens(cookies_path)
    if not auth_token:
        raise SystemExit(f"no auth_token in {cookies_path}")
    body: dict = {"text": text, "auth_token": auth_token}
    if ct0:
        body["ct0"] = ct0
    if dry:
        return {"dry": True, "chars": len(text)}
    ok, reason = allow("tweet/create")
    if not ok:
        raise SystemExit(f"budget stop: {reason}")
    r = httpx.post(f"{API}/twitter/tweet/create",
                   headers={"Authorization": "Bearer " + os.environ["GETXAPI_KEY"]},
                   json=body, timeout=60)
    r.raise_for_status()
    log("tweet/create")
    return r.json()


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    cookies = "/opt/data/projects/uny-x/cookies.json"
    for a in sys.argv[1:]:
        if a.startswith("--cookies="):
            cookies = a.split("=", 1)[1]
    if not args and not dry:
        raise SystemExit('usage: getxapi.py "text" [--cookies PATH] [--dry]')
    out = post(args[0] if args else "", cookies, dry)
    print(json.dumps(out, indent=1)[:600])


if __name__ == "__main__":
    main()
