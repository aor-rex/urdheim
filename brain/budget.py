"""Urdheim spend guard: daily + monthly caps on billable GetXAPI calls.

Every billable call site (backfill/poll in watcher/getxapi.py, posting in
poster/getxapi.py) checks budget.allow(kind) first and logs after. Ledger
is a local JSONL file — survives restarts, auditable, never leaves the box.

Env (defaults target ~$1-2/mo ≈ ₦1,500–3,000):
  BUDGET_MONTHLY_USD=2.0    hard stop for the calendar month
  BUDGET_DAILY_READS=40     backfill/poll calls/day (~800 tweets/day)
  BUDGET_DAILY_WRITES=7     posts/day
  BUDGET_LEDGER=watcher/spend.jsonl
Costs (per GetXAPI pricing):
  user/tweets  $0.001/call · tweet/create $0.002/call · monitors = plan, $0
"""
import datetime as _dt
import json as _json
import os as _os

COSTS = {
    "user/tweets": 0.001,
    "monitor/add": 0.0,
    "monitor/remove": 0.0,
    "monitor/list": 0.0,
    "tweet/create": 0.002,
}

READ_KINDS = {"user/tweets", "monitor/add", "monitor/remove", "monitor/list"}
WRITE_KINDS = {"tweet/create"}


def _ledger() -> str:
    return _os.environ.get("BUDGET_LEDGER", "watcher/spend.jsonl")


def _today() -> str:
    return _dt.date.today().isoformat()


def _month() -> str:
    return _dt.date.today().strftime("%Y-%m")


def log(endpoint: str) -> None:
    with open(_ledger(), "a") as f:
        f.write(_json.dumps({
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "day": _today(),
            "month": _month(),
            "endpoint": endpoint,
            "cost": COSTS.get(endpoint, 0.0),
        }) + "\n")


def spent(day: str | None = None, month: str | None = None) -> float:
    total = 0.0
    path = _ledger()
    if not _os.path.exists(path):
        return 0.0
    for line in open(path):
        try:
            r = _json.loads(line)
        except Exception:
            continue
        if day and r.get("day") != day:
            continue
        if month and r.get("month") != month:
            continue
        total += float(r.get("cost", 0.0))
    return round(total, 4)


def writes_today() -> int:
    n = 0
    path = _ledger()
    if not _os.path.exists(path):
        return 0
    for line in open(path):
        try:
            r = _json.loads(line)
        except Exception:
            continue
        if r.get("day") == _today() and r.get("endpoint") in WRITE_KINDS:
            n += 1
    return n


def reads_today() -> int:
    n = 0
    path = _ledger()
    if not _os.path.exists(path):
        return 0
    for line in open(path):
        try:
            r = _json.loads(line)
        except Exception:
            continue
        if r.get("day") == _today() and r.get("endpoint") in READ_KINDS:
            n += 1
    return n


def allow(endpoint: str) -> tuple[bool, str]:
    """(ok, reason). Call BEFORE firing; call log() AFTER success."""
    if endpoint in WRITE_KINDS:
        cap = int(_os.environ.get("BUDGET_DAILY_WRITES", "7"))
        if writes_today() >= cap:
            return False, f"daily write cap hit ({cap})"
    if endpoint in READ_KINDS:
        cap = int(_os.environ.get("BUDGET_DAILY_READS", "40"))
        if reads_today() >= cap:
            return False, f"daily read cap hit ({cap})"
    cap_m = float(_os.environ.get("BUDGET_MONTHLY_USD", "2.0"))
    if spent(month=_month()) + COSTS.get(endpoint, 0.0) > cap_m:
        return False, f"monthly $${cap_m} cap hit"
    return True, "ok"
