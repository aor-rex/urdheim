"""Urdheim read API: postgres -> JSON. The dashboard fetches live —
no export step, no rebuild. Scales: same endpoints serve the site,
the bot, and future API consumers.

Run: uvicorn api.server:app --port 8091
Env: DB_URL
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import psycopg  # noqa: E402
from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402
import base64
import hashlib
import hmac
import secrets  # noqa: E402
import urllib.parse  # noqa: E402

app = FastAPI(title="urdheim-api")
_origins = [o.strip() for o in
            os.environ.get("CORS_ORIGINS",
                           "http://localhost:8092,http://127.0.0.1:8092").split(",")
            if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)


# --- X sign-in (OAuth 2.0 PKCE). handle lands in allowed_users,
# --- pfp/bio in profiles. session = HMAC cookie, no server store.

def _sess_secret() -> str:
    return os.environ.get("SESSION_SECRET", "")


def _app_url() -> str:
    return os.environ.get("APP_URL", "https://urdheim.zone.id").rstrip("/")


def _callback_url() -> str:
    return os.environ.get("OAUTH_CALLBACK", _app_url() + "/api/auth/callback")


def _sign(handle: str) -> str:
    mac = hmac.new(_sess_secret().encode(), handle.encode(),
                   hashlib.sha256).hexdigest()[:32]
    raw = f"{handle}.{mac}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def _verify(token: str) -> str | None:
    try:
        handle, mac = base64.urlsafe_b64decode(token.encode()).decode().split(".")
        want = hmac.new(_sess_secret().encode(), handle.encode(),
                        hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(mac, want):
            return handle
    except Exception:
        pass
    return None


def session_handle(request: Request) -> str | None:
    if not _sess_secret():
        return None
    return _verify(request.cookies.get("urdheim_sess", ""))


@app.get("/api/auth/login")
def auth_login() -> RedirectResponse:
    cid = os.environ.get("X_CLIENT_ID", "")
    if not cid:
        raise HTTPException(500, "x sign-in not configured")
    state = secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(64)
    chal = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": cid,
        "redirect_uri": _callback_url(),
        "scope": "tweet.read users.read offline.access",
        "state": state, "code_challenge": chal,
        "code_challenge_method": "S256"})
    res = RedirectResponse("https://x.com/i/oauth2/authorize?" + params)
    res.set_cookie("urdheim_pkce", f"{state}.{verifier}", httponly=True,
                   secure=True, samesite="lax", max_age=600, path="/")
    return res


@app.get("/api/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    pkce = request.cookies.get("urdheim_pkce", "")
    good = RedirectResponse(_app_url() + "/my")
    bad = RedirectResponse(_app_url() + "/signin?err=1")
    if not code or not state or "." not in pkce:
        return bad
    want_state, verifier = pkce.split(".", 1)
    if not hmac.compare_digest(state, want_state):
        return bad
    cid = os.environ.get("X_CLIENT_ID", "")
    csec = os.environ.get("X_CLIENT_SECRET", "")
    try:
        tr = httpx.post(
            "https://api.x.com/2/oauth2/token",
            auth=(cid, csec),
            data={"grant_type": "authorization_code", "code": code,
                  "redirect_uri": _callback_url(), "code_verifier": verifier},
            timeout=20)
        tok = tr.json()
        access = tok.get("access_token", "")
        refresh = tok.get("refresh_token", "")
        if not access:
            return bad
        mr = httpx.get(
            "https://api.x.com/2/users/me?user.fields="
            "profile_image_url,description,public_metrics,verified",
            headers={"Authorization": "Bearer " + access}, timeout=20)
        me = mr.json().get("data", {})
        handle = (me.get("username") or "").lower()
        if not handle:
            return bad
        pm = me.get("public_metrics") or {}
        with conn() as cn, cn.cursor() as cur:
            cur.execute(
                """INSERT INTO allowed_users (handle, x_id, nudged, refresh_token)
                   VALUES (%s, %s, TRUE, %s)
                   ON CONFLICT (handle) DO UPDATE SET
                     x_id = EXCLUDED.x_id, nudged = TRUE,
                     refresh_token = EXCLUDED.refresh_token""",
                (handle, me.get("id", ""), refresh))
            cur.execute(
                """INSERT INTO profiles
                     (handle, name, avatar, bio, followers, following, verified)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (handle) DO UPDATE SET
                     name = EXCLUDED.name, avatar = EXCLUDED.avatar,
                     bio = EXCLUDED.bio, followers = EXCLUDED.followers,
                     following = EXCLUDED.following,
                     verified = EXCLUDED.verified, updated_at = now()""",
                (handle, me.get("name") or handle,
                 me.get("profile_image_url") or "",
                 me.get("description") or "",
                 (pm.get("followers_count") or 0),
                 (pm.get("following_count") or 0),
                 bool(me.get("verified"))))
            cn.commit()
    except Exception:
        return bad
    good.set_cookie("urdheim_sess", _sign(handle), httponly=True,
                    secure=True, samesite="lax", max_age=30 * 86400, path="/")
    good.delete_cookie("urdheim_pkce", path="/")
    return good


@app.get("/api/auth/me")
def auth_me(request: Request) -> dict:
    h = session_handle(request)
    if not h:
        return {"handle": None}
    return {"handle": h}


def verify_turnstile(token: str) -> bool:
    secret = os.environ.get("TURNSTILE_SECRET", "")
    if not secret:
        return False
    try:
        r = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token}, timeout=15)
        return bool(r.json().get("success"))
    except Exception:
        return False


@app.post("/api/snitch")
def snitch(body: dict, request: Request) -> dict:
    url = (body.get("post_url") or "").strip()
    handle = (body.get("handle") or "").strip().lstrip("@")
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "web"))
    if not url.startswith("https://x.com/") and not url.startswith("https://twitter.com/"):
        raise HTTPException(400, "post link must be an x.com url")
    if not verify_turnstile(body.get("turnstile") or ""):
        raise HTTPException(403, "bot check failed")
    with conn() as cn, cn.cursor() as cur:
        cur.execute("SELECT id FROM submissions WHERE post_url = %s", (url,))
        if cur.fetchone():
            return {"ok": True, "duplicate": True}
        cur.execute(
            """INSERT INTO submissions (post_url, suggested_caller,
                                        reporter_ip, status)
               VALUES (%s, %s, %s, 'pending') RETURNING id""",
            (url, handle or None, ip))
        sid = cur.fetchone()[0]
        cn.commit()
    return {"ok": True, "id": sid}


def conn():
    return psycopg.connect(os.environ["DB_URL"])


def pct(mult: float | None) -> str:
    if mult is None:
        return "—"
    sign = "+" if mult >= 1 else "−"
    return f"{sign}{abs(mult - 1) * 100:.0f}%"


def shape_call(row: dict) -> dict:
    """One call + its return multiple from peak, state from the snapshotter."""
    at = row.get("price_at_call") or None
    now = row.get("now") or None
    mult = (now / at) if at and now else None
    return {
        "coin": row.get("coin"), "mint": row.get("mint"),
        "chain": row.get("chain"), "handle": row.get("handle"),
        "then": at, "now": now, "mult": mult, "ret": pct(mult),
        "good": bool(mult and mult >= 1),
        "peak": row.get("peak"), "peak_x": row.get("peak_x"),
        "state": row.get("state") or "open",
        "called_at": str(row.get("called_at") or "")[:10],
        "post_url": row.get("post_url"),
    }


def score(calls: list[dict]) -> dict:
    """Leaderboard math on peak_x (median, never best): spray-and-pray
    callers can't top the board with one lucky runner among fifty rugs."""
    xs = sorted(c["peak_x"] for c in calls if c.get("peak_x"))
    green = sum(1 for c in calls if (c.get("peak_x") or 0) >= 2)
    red = sum(1 for c in calls if c.get("state") in ("condemned", "rugged"))
    med = xs[len(xs) // 2] if xs else None
    avg = round((med - 1) * 100) if med else 0
    if len(xs) >= 3 and green > red:
        seal = "VINDICATED"
    elif len(xs) >= 3 and red > green:
        seal = "CONDEMNED"
    else:
        seal = "UNDECIDED"
    return {"green": green, "red": red, "avg": avg,
            "seal": seal, "kind": "clean" if green >= red else "guilty"}


def verdict_sentence(handle: str, s: dict, n: int) -> str:
    if n == 0:
        return f"@{handle} is on the watchlist. No scored calls yet."
    if s["seal"] == "VINDICATED":
        return (f"@{handle}: {s['green']} of {n} calls ran 2x or better, "
                f"median peak {s['avg']:+.0f}%. The record holds.")
    if s["seal"] == "CONDEMNED":
        return (f"@{handle}: {s['red']} of {n} calls condemned, "
                f"median peak {s['avg']:+.0f}%. Fade everything.")
    return (f"@{handle}: {n} calls on record, jury still out "
            f"({s['green']} green, {s['red']} red).")


def caller_row(handle: str, calls: list[dict], rank: str) -> dict:
    s = score(calls)
    ordered = sorted(calls, key=lambda c: (c["mult"] is None,
                                           c["mult"] or 0))
    worst = ordered[0] if ordered else None
    return {
        "handle": handle, "rank": rank, "calls": len(calls),
        "chains": sorted({c["chain"] for c in calls}),
        "verdict": verdict_sentence(handle, s, len(calls)),
        "worst": ({
            "coin": worst["coin"], "then": worst["then"],
            "now": worst["now"], "ret": worst["ret"],
            "good": worst["good"]} if worst else None),
        "log": [[f"{c['coin']} · {c['called_at']}", c["ret"], c["good"]]
                for c in sorted(calls, key=lambda c: c["called_at"],
                                reverse=True)],
        **s,
    }


def fetch_calls(cur, where: str, arg) -> list[dict]:
    cur.execute(f"""
        SELECT c.coin, c.mint, c.chain, h.handle, c.price_at_call,
               c.called_at, c.post_url, c.filer_handle, c.filed_via,
               c.likes, c.reposts, c.quotes, c.views,
               c.peak, c.peak_x, c.state,
               (SELECT s.price FROM snapshots s
                 WHERE s.call_id = c.id ORDER BY s.taken_at DESC LIMIT 1) AS now
        FROM calls c JOIN callers h ON h.id = c.caller_id
        WHERE {where} ORDER BY c.called_at DESC""", (arg,))
    cols = [d[0] for d in cur.description]
    return [shape_call(dict(zip(cols, r))) for r in cur.fetchall()]


def profile_map(cur, handles: set[str]) -> dict:
    """Cached X identity for a set of handles. Missing rows → bare stub."""
    if not handles:
        return {}
    cur.execute("SELECT handle, name, avatar, bio, followers, following,"
                " verified FROM profiles WHERE handle = ANY(%s)",
                (list(handles),))
    out = {r[0]: {"handle": r[0], "name": r[1] or r[0], "avatar": r[2] or "",
                  "bio": r[3] or "", "followers": r[4] or 0,
                  "following": r[5] or 0, "verified": bool(r[6])}
           for r in cur.fetchall()}
    for h in handles:
        out.setdefault(h, {"handle": h, "name": h, "avatar": "", "bio": "",
                           "followers": 0, "following": 0, "verified": False})
    return out


def shape_receipt(c: dict, people: dict) -> dict:
    viral = (c.get("views") or 0) >= 40000
    seal = {"vindicated": "VINDICATED", "condemned": "CONDEMNED",
            "rugged": "RUGGED"}.get(c.get("state") or "open", "UNDECIDED")
    return {
        "coin": c["coin"], "mint": c["mint"], "chain": c["chain"],
        "caller": people.get(c["handle"], {"handle": c["handle"]}),
        "filer": people.get(c.get("filer_handle") or c["handle"],
                            {"handle": c.get("filer_handle") or c["handle"]}),
        "filed_via": c.get("filed_via") or "seed",
        "then": c["then"], "now": c["now"], "mult": c["mult"],
        "peak": c.get("peak"), "peak_x": c.get("peak_x"),
        "ret": c["ret"], "good": c["good"],
        "seal": seal,
        "viral": viral,
        "eng": {"likes": c.get("likes") or 0, "reposts": c.get("reposts") or 0,
                "quotes": c.get("quotes") or 0, "views": c.get("views") or 0},
        "called_at": c["called_at"], "post_url": c["post_url"],
        "ts": c.get("ts") or c["called_at"],
    }


@app.get("/api/feed")
def feed(limit: int = 30) -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("""
            SELECT c.coin, c.mint, c.chain, h.handle, c.price_at_call,
                   c.called_at, c.post_url, c.filer_handle, c.filed_via,
                   c.likes, c.reposts, c.quotes, c.views,
                   c.peak, c.peak_x, c.state,
                   (SELECT s.price FROM snapshots s
                     WHERE s.call_id = c.id ORDER BY s.taken_at DESC LIMIT 1) AS now
            FROM calls c JOIN callers h ON h.id = c.caller_id
            ORDER BY c.called_at DESC LIMIT %s""", (min(limit, 100),))
        cols = [d[0] for d in cur.description]
        raws = [dict(zip(cols, r)) for r in cur.fetchall()]
        people = profile_map(cur, {r["handle"] for r in raws} |
                             {r["filer_handle"] for r in raws
                              if r.get("filer_handle")})
        receipts = []
        for raw in raws:
            c = shape_call(raw)
            c.update({k: raw.get(k) for k in
                      ("filer_handle", "filed_via", "likes", "reposts",
                       "quotes", "views")})
            c["ts"] = str(raw.get("called_at") or "")
            receipts.append(shape_receipt(c, people))
    return {"receipts": receipts}


@app.get("/api/profile/{handle}")
def profile(handle: str) -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("""
            SELECT c.coin, c.mint, c.chain, h.handle, c.price_at_call,
                   c.called_at, c.post_url, c.filer_handle, c.filed_via,
                   c.likes, c.reposts, c.quotes, c.views,
                   c.peak, c.peak_x, c.state,
                   (SELECT s.price FROM snapshots s
                     WHERE s.call_id = c.id ORDER BY s.taken_at DESC LIMIT 1) AS now
            FROM calls c JOIN callers h ON h.id = c.caller_id
            WHERE h.handle = %s OR c.filer_handle = %s
            ORDER BY c.called_at DESC""", (handle, handle))
        cols = [d[0] for d in cur.description]
        raws = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.execute("SELECT 1 FROM profiles WHERE handle = %s", (handle,))
        known = bool(cur.fetchone())
        if not raws and not known:
            raise HTTPException(404, f"no record on @{handle} yet")
        people = profile_map(cur, {r["handle"] for r in raws} |
                             {r["filer_handle"] for r in raws
                              if r.get("filer_handle")} | {handle})
        receipts = []
        for raw in raws:
            c = shape_call(raw)
            c.update({k: raw.get(k) for k in
                      ("filer_handle", "filed_via", "likes", "reposts",
                       "quotes", "views")})
            c["ts"] = str(raw.get("called_at") or "")
            receipts.append(shape_receipt(c, people))
        filed = sum(1 for r in raws
                    if (r.get("filer_handle") or r["handle"]) == handle)
        scored = sorted(r["mult"] for r in receipts if r["mult"] is not None)
        med = scored[len(scored) // 2] if scored else None
        avg = round((med - 1) * 100) if med else 0
    return {"profile": people[handle], "stats": {
        "filed": filed, "verified": len(scored), "avg": round(avg),
        "scored": len(scored)}, "receipts": receipts}


@app.get("/api/leaderboard")
def leaderboard() -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("SELECT handle FROM callers ORDER BY added_at")
        handles = [r[0] for r in cur.fetchall()]
        people = profile_map(cur, set(handles))
        if not handles:
            return {"callers": []}
        cur.execute("""
            SELECT c.coin, c.mint, c.chain, h.handle, c.price_at_call,
                   c.called_at, c.post_url, c.filer_handle, c.filed_via,
                   c.likes, c.reposts, c.quotes, c.views,
                   c.peak, c.peak_x, c.state,
                   (SELECT s.price FROM snapshots s
                     WHERE s.call_id = c.id ORDER BY s.taken_at DESC LIMIT 1) AS now
            FROM calls c JOIN callers h ON h.id = c.caller_id
            ORDER BY c.called_at DESC""")
        cols = [d[0] for d in cur.description]
        by_caller: dict[str, list[dict]] = {h: [] for h in handles}
        for r in cur.fetchall():
            c = shape_call(dict(zip(cols, r)))
            by_caller.setdefault(c["handle"], []).append(c)
        scored = [(h, score(by_caller.get(h, []))) for h in handles
                 if by_caller.get(h)]
        if not scored:
            return {"callers": []}
        scored.sort(key=lambda t: (t[1]["avg"], t[1]["green"]), reverse=True)
        rows = []
        for i, (h, _) in enumerate(scored, 1):
            row = caller_row(h, by_caller.get(h, []), str(i))
            row["profile"] = people.get(h, {"handle": h})
            rows.append(row)
    return {"callers": rows}


@app.get("/api/caller/{handle}")
def caller(handle: str) -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("SELECT 1 FROM callers WHERE handle = %s", (handle,))
        if not cur.fetchone():
            raise HTTPException(404, f"no file on @{handle} yet")
        calls = fetch_calls(cur, "h.handle = %s", handle)
    return caller_row(handle, calls, "—")


@app.get("/api/coin/{mint}")
def coin(mint: str) -> dict:
    with conn() as cn, cn.cursor() as cur:
        calls = fetch_calls(cur, "c.mint = %s", mint)
        if not calls:
            raise HTTPException(404, "no record on this coin yet")
        cur.execute("""
            SELECT MAX(mcap), MAX(taken_at) FROM snapshots s
            JOIN calls c ON c.id = s.call_id WHERE c.mint = %s""", (mint,))
        peak, _ = cur.fetchone()
        cur.execute("""
            SELECT price, mcap FROM snapshots s JOIN calls c ON c.id = s.call_id
            WHERE c.mint = %s ORDER BY s.taken_at DESC LIMIT 1""", (mint,))
        last = cur.fetchone()
    first = calls[-1]
    now_mcap = (last or [0, 0])[1] or 0
    peak = peak or now_mcap or first["now"] or 0
    drop = (now_mcap / peak) if peak and now_mcap else None
    return {
        "coin": first["coin"], "mint": mint, "chain": first["chain"],
        "dead": bool(drop is not None and drop < 0.2),
        "delta": pct(drop), "peak": peak, "now": now_mcap,
        "touchers": [{
            "handle": c["handle"],
            "note": f"called {c['called_at']}",
            "timing": ("GREEN" if c["good"] else "RED") if c["mult"] is not None else "PENDING",
            "top": bool(c["mult"] is not None and not c["good"]),
        } for c in calls],
        "note": (f"{len(calls)} tracked caller(s). "
                 + (f"Down {pct(drop)} from peak." if drop and drop < 1
                    else "Holding above call levels.")),
    }


@app.get("/api/stats")
def stats() -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM callers")
        callers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM calls")
        calls = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM snapshots")
        snaps = cur.fetchone()[0]
    return {"callers": callers, "calls": calls, "snapshots": snaps}


@app.get("/health")
def health() -> dict:
    return {"ok": True}
