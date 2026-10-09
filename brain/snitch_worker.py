"""Snitch worker: pending submissions -> verified calls.

Reads a snitched post (free via uny-x), runs the detective, and either
records the call (accepted) or bins it (rejected). Three accepted
nominations for an untracked handle enroll it on the watchlist
(watched table) — then the normal poll backfills its history.

Run one-shot: .venv/bin/python brain/snitch_worker.py [--limit 20]
Env: DB_URL, LISTENER_COOKIES (read path, free), OPENCODE_* (verdicts).
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg  # noqa: E402
from unyx import UnyxClient  # noqa: E402

from brain.detective import classify, record_call  # noqa: E402
from listener.mentions import enroll_caller, parse_raw_tweet  # noqa: E402
from watcher.common import is_candidate  # noqa: E402

POST_RE = re.compile(r"(?:x|twitter)\.com/\w+/status/(\d+)")


def fetch_post(client: UnyxClient, url: str) -> tuple[str, str, str] | None:
    m = POST_RE.search(url or "")
    if not m:
        return None
    try:
        tw = client.read(m.group(1))
    except Exception as e:
        print(f"read failed {m.group(1)}: {e}")
        return None
    if not tw:
        return None
    author = ((tw.get("author") or {}).get("screen_name")
              or tw.get("screen_name"))
    text = tw.get("text") or tw.get("full_text") or ""
    if not author or not text:
        # raw TweetResultByRestId blob: parse the real fields out of it
        parsed = parse_raw_tweet(tw.get("raw", {}) if isinstance(tw, dict) else {})
        if parsed:
            author = author or parsed["author"]
            text = text or parsed["text"]
    return author or "?", m.group(1), text


def process(limit: int = 20) -> dict:
    client = UnyxClient()
    cookies = (os.environ.get("LISTENER_COOKIES")
               or os.environ.get("POSTER_COOKIES") or "")
    if cookies and not client.login_from_cookies(cookies):
        raise SystemExit("cookie login failed — re-export cookies.json")
    out = {"accepted": 0, "rejected": 0, "enrolled": []}
    with psycopg.connect(os.environ["DB_URL"]) as cn, cn.cursor() as cur:
        cur.execute("""SELECT id, post_url, suggested_caller, filer_handle,
                              caller_post_ts, tag_post_id, reporter_ip
                       FROM submissions
                       WHERE status = 'pending' ORDER BY id LIMIT %s""",
                    (limit,))
        rows = cur.fetchall()
        for sid, url, suggested, filer, call_post_ts, tag_pid, reporter in rows:
            got = fetch_post(client, url)
            if not got or not is_candidate(got[2]):
                cur.execute("UPDATE submissions SET status='rejected' WHERE id=%s",
                            (sid,))
                out["rejected"] += 1
                continue
            author, post_id, text = got
            try:
                v = classify(author, text)
            except Exception as e:
                from brain.budget import BudgetStop
                if isinstance(e, BudgetStop):
                    print(f"snitch stop: {e} (next round picks it up)")
                    break
                cur.execute("UPDATE submissions SET status='rejected' WHERE id=%s",
                            (sid,))
                out["rejected"] += 1
                print(f"snitch skip {sid}: {str(e)[:120]}")
                continue
            if v.get("verdict") != "call":
                cur.execute("UPDATE submissions SET status='rejected' WHERE id=%s",
                            (sid,))
                out["rejected"] += 1
                continue
            from watcher.common import find_cas, snapshot_price, detect_chain
            from watcher.history import history_price
            import time as _time
            mints = find_cas(text)
            if not mints:
                cur.execute("UPDATE submissions SET status='rejected' WHERE id=%s",
                            (sid,))
                out["rejected"] += 1
                continue
            mint = mints[0]
            chain = detect_chain(mint)
            call_ts = (call_post_ts.timestamp()
                       if call_post_ts is not None else None)
            snap, estimated = None, False
            if call_ts and _time.time() - call_ts > 300:
                snap = history_price(mint, chain, call_ts, patient=True)
            if snap:
                estimated = bool(snap.get("estimated", True))
            else:
                snap = snapshot_price(mint)
                estimated = bool(call_ts)  # live fallback for an old call
            call_id = record_call(
                {"author": author, "post_id": post_id, "text": text,
                 "mint": mint, "chain": chain, "snapshot": snap,
                 "called_at": call_post_ts,
                 "entry_estimated": estimated,
                 "filer": filer,
                 "filed_via": ("x-mention" if reporter == "x-mention"
                               else "form"),
                 "client": client}, v)
            if call_id and filer and tag_pid:
                cur.execute(
                    """UPDATE filer_entries SET call_id = %s
                       WHERE filer_handle = %s AND tag_post_id = %s
                       AND call_id IS NULL""",
                    (call_id, filer, tag_pid))
            cur.execute("UPDATE submissions SET status='accepted' WHERE id=%s",
                        (sid,))
            out["accepted"] += 1
            # 3 accepted nominations naming the same handle enroll it.
            # Mention rows store "author:mint", form rows the handle.
            # Fires on the 3rd (enroll_caller dedupes after that).
            nominated = (suggested or "").split(":")[0] or author
            cur.execute("""SELECT COUNT(*) FROM submissions
                           WHERE split_part(suggested_caller, ':', 1) = %s
                           AND status = 'accepted'""",
                        (nominated,))
            if (cur.fetchone()[0] or 0) == 3:
                out["enrolled"].append(nominated)
                print(enroll_caller(nominated))
        cn.commit()
    client.close()
    return out


if __name__ == "__main__":
    n = int((sys.argv[sys.argv.index("--limit") + 1]
             if "--limit" in sys.argv else 20))
    print(process(n))
