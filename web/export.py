"""Urdheim db->web exporter: postgres rows into web-next/lib/data.js.

Reads callers + calls + latest snapshot per call, computes per-caller
stats (total/green/red/avg/worst/log/chains), writes the same shape the
pages already render. Mock data dies the day this runs on real rows.

Usage: DB_URL=postgresql://... .venv/bin/python web/export.py
Test (no postgres): .venv/bin/python web/export_test.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PAGE = os.path.join(os.path.dirname(__file__), "..", "web-next", "lib", "data.js")


def fetch_rows():
    import psycopg

    with psycopg.connect(os.environ["DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT c.handle, cl.coin, cl.mint, cl.chain,
                      cl.price_at_call, cl.called_at, cl.post_id,
                      s.price AS now_price
               FROM calls cl
               JOIN callers c ON c.id = cl.caller_id
               LEFT JOIN LATERAL (
                 SELECT price FROM snapshots WHERE call_id = cl.id
                 ORDER BY taken_at DESC LIMIT 1
               ) s ON true
               ORDER BY c.handle, cl.called_at"""
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def build(rows: list[dict]) -> tuple[list[dict], dict]:
    by_caller: dict[str, list[dict]] = {}
    for r in rows:
        by_caller.setdefault(r["handle"], []).append(r)
    callers = []
    for handle, calls in by_caller.items():
        scored = []
        for c in calls:
            then, now = c["price_at_call"], c.get("now_price")
            if then and now:
                scored.append((c, (now - then) / then * 100))
        green = sum(1 for _, ret in scored if ret >= 0)
        red = len(scored) - green
        avg = round(sum(r for _, r in scored) / len(scored)) if scored else 0
        worst = min(scored, key=lambda t: t[1], default=None)
        log = [[f"{c['coin']} · {str(c['called_at'])[:10]}",
                f"{ret:+.0f}%".replace("+", "+"), ret >= 0]
               for c, ret in sorted(scored, key=lambda t: str(t[0]["called_at"]),
                                    reverse=True)[:6]]
        callers.append({
            "handle": handle,
            "chains": sorted({c["chain"] or "solana" for c in calls}),
            "calls": len(calls),
            "green": green,
            "red": red,
            "avg": avg,
            "seal": "CONDEMNED" if scored and green == 0 and len(scored) >= 5
                   else "VINDICATED" if scored and red == 0 and len(scored) >= 5
                   else "UNDECIDED",
            "kind": "guilty" if scored and green <= red else "clean",
            "verdict": f"{len(calls)} tracked calls, {green} green. "
                       "Verdict written by Heimdall.",
            "worst": {
                "coin": worst[0]["coin"], "ret": f"{worst[1]:+.0f}%",
                "good": worst[1] >= 0,
            } if worst else {"coin": "—", "ret": "—", "good": False},
            "log": log,
        })
    callers.sort(key=lambda c: c["avg"])
    for i, c in enumerate(callers, 1):
        c["rank"] = ["I", "II", "III", "IV", "V", "VI", "VII"][min(i - 1, 6)]

    coins: dict[str, dict] = {}
    for r in rows:
        mint = r["mint"]
        c = coins.setdefault(mint, {
            "coin": r["coin"], "mint": mint, "chain": r["chain"] or "solana",
            "first": None, "touchers": [],
        })
        if r["price_at_call"] and (c["first"] is None or
                                   str(r["called_at"]) < str(c["first_at"])):
            c["first"] = r["price_at_call"]
            c["first_at"] = str(r["called_at"])
        c["touchers"].append(r)
    for mint, c in coins.items():
        now = next((t.get("now_price") for t in c["touchers"]
                    if t.get("now_price")), None) or c["first"] or 0
        first = c["first"] or now or 1
        delta = (now - first) / first * 100 if first else 0
        c["now"] = f"${now:.8g}"
        c["peak"] = c["now"]  # peak tracking arrives with hourly snapshots
        c["delta"] = f"{delta:+.0f}%"
        c["note"] = (f"{len(c['touchers'])} tracked call(s). "
                     "Full history on the leaderboard.")
        touchers = []
        for t in c["touchers"]:
            then = t["price_at_call"] or 0
            ret = (now - then) / then * 100 if then and now else 0
            touchers.append({
                "handle": t["handle"],
                "note": f"called @ ${then:.8g}" if then else "called",
                "timing": f"{ret:+.0f}%",
                "top": ret < 0,
            })
        c["touchers"] = touchers
        c.pop("first", None); c.pop("first_at", None)
    return callers, coins


def render(callers: list[dict], coins: dict) -> str:
    return ("// GENERATED from postgres by web/export.py — do not hand-edit.\n"
            "export const callers = " + json.dumps(callers, indent=2) + ";\n\n"
            "export const coins = " + json.dumps(coins, indent=2) + ";\n\n"
            "export const X_URL = 'https://x.com/Urdheim';\n\n"
            "export const fmtAvg = (v) => (v > 0 ? '+' : v < 0 ? '−' : '')"
            " + Math.abs(v) + '%';\n")


def main() -> None:
    callers, coins = build(fetch_rows())
    with open(PAGE, "w") as f:
        f.write(render(callers, coins))
    print(f"exported {len(callers)} callers, {len(coins)} coins -> {PAGE}")


if __name__ == "__main__":
    main()
