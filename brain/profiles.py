"""Profile cache: X identity for callers + filers, one free lookup each.

renders never touch X. cache at file time, refresh counts on poll.
OAuth will write the signed-in user's row directly (no lookup needed).
"""
import os
import re

import psycopg  # noqa: E402

ZALGO = re.compile(r"[\u0300-\u036f\u034f]")


def clean_name(name, fallback: str) -> str:
    name = ZALGO.sub("", (name or "")).strip()
    return name if name else fallback


def upsert_profile(cur, user: dict) -> None:
    cur.execute(
        """INSERT INTO profiles(handle, name, avatar, bio, followers,
                                following, verified, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, now())
           ON CONFLICT (handle) DO UPDATE SET
             name = EXCLUDED.name, avatar = EXCLUDED.avatar,
             bio = EXCLUDED.bio, followers = EXCLUDED.followers,
             following = EXCLUDED.following, verified = EXCLUDED.verified,
             updated_at = now()""",
        (user["screen_name"], clean_name(user.get("name"), user["screen_name"]),
         user.get("avatar") or "", user.get("description") or "",
         user.get("followers_count") or 0, user.get("following_count") or 0,
         bool(user.get("is_verified"))),
    )


def ensure_profile(handle: str, client=None) -> dict | None:
    """Return cached profile, fetching + caching on first sight."""
    if not handle:
        return None
    with psycopg.connect(os.environ["DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute("SELECT handle, name, avatar, bio, followers, following,"
                    " verified FROM profiles WHERE handle = %s", (handle,))
        row = cur.fetchone()
        if row:
            conn.commit()
            return dict(zip(
                ["handle", "name", "avatar", "bio", "followers", "following",
                 "verified"], row))
        if client is None:
            return None
        try:
            user = client.user(handle)
        except Exception as e:
            print(f"profile fetch failed @{handle}: {e}")
            return None
        upsert_profile(cur, user)
        conn.commit()
        return {"handle": user["screen_name"],
                "name": clean_name(user.get("name"), user["screen_name"]),
                "avatar": user.get("avatar") or "",
                "bio": user.get("description") or "",
                "followers": user.get("followers_count") or 0,
                "following": user.get("following_count") or 0,
                "verified": bool(user.get("is_verified"))}
