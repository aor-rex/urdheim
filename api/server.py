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
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

app = FastAPI(title="urdheim-api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8092", "http://127.0.0.1:8092"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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
def snitch(body: dict) -> dict:
    url = (body.get("post_url") or "").strip()
    handle = (body.get("handle") or "").strip().lstrip("@")
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
            (url, handle or None, "web"))
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
    """One call + its return multiple from the latest snapshot."""
    at = row.get("price_at_call") or None
    now = row.get("now") or None
    mult = (now / at) if at and now else None
    return {
        "coin": row.get("coin"), "mint": row.get("mint"),
        "chain": row.get("chain"), "handle": row.get("handle"),
        "then": at, "now": now, "mult": mult, "ret": pct(mult),
        "good": bool(mult and mult >= 1),
        "called_at": str(row.get("called_at") or "")[:10],
        "post_url": row.get("post_url"),
    }


def score(calls: list[dict]) -> dict:
    scored = [c for c in calls if c["mult"] is not None]
    green = sum(1 for c in scored if c["good"])
    red = len(scored) - green
    avg = (sum((c["mult"] - 1) * 100 for c in scored) / len(scored)) if scored else 0
    if len(scored) >= 3 and green > red:
        seal = "VINDICATED"
    elif len(scored) >= 3 and red > green:
        seal = "CONDEMNED"
    else:
        seal = "UNDECIDED"
    return {"green": green, "red": red, "avg": round(avg),
            "seal": seal, "kind": "clean" if green >= red else "guilty"}


def verdict_sentence(handle: str, s: dict, n: int) -> str:
    if n == 0:
        return f"@{handle} is on the watchlist. No scored calls yet."
    if s["seal"] == "VINDICATED":
        return (f"@{handle}: {s['green']} of {n} scored calls green, "
                f"avg {s['avg']:+.0f}%. The record holds.")
    if s["seal"] == "CONDEMNED":
        return (f"@{handle}: {s['red']} of {n} scored calls red, "
                f"avg {s['avg']:+.0f}%. Fade everything.")
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
               c.called_at, c.post_url,
               (SELECT s.price FROM snapshots s
                 WHERE s.call_id = c.id ORDER BY s.taken_at DESC LIMIT 1) AS now
        FROM calls c JOIN callers h ON h.id = c.caller_id
        WHERE {where} ORDER BY c.called_at DESC""", (arg,))
    cols = [d[0] for d in cur.description]
    return [shape_call(dict(zip(cols, r))) for r in cur.fetchall()]


@app.get("/api/leaderboard")
def leaderboard() -> dict:
    with conn() as cn, cn.cursor() as cur:
        cur.execute("SELECT handle FROM callers ORDER BY added_at")
        handles = [r[0] for r in cur.fetchall()]
        rows = []
        for i, h in enumerate(handles, 1):
            calls = fetch_calls(cur, "h.handle = %s", h)
            rows.append(caller_row(h, calls, str(i)))
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
