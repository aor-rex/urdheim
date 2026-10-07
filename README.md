# Urdheim — KOL accountability engine for Solana memecoins.

Every call leaves a record. `docs/implementation.md` is the source of truth.

## Layout

- `docs/implementation.md` — full plan (phases, decisions, MVP cutoff)
- `schema.sql` — postgres: callers, calls, snapshots, submissions
- `watcher/` — stream watcher: twitterapi.io filter stream, regex CAs, snapshot price, queue
- `brain/` — detective (API verdicts), repricer + writer land here next
- `web/` — leaderboard + pages land here (phase 3)

## Local run (full loop, real postgres)

```bash
# 0. one-time: venv + postgres 17 (userland, lives in /opt/data/pg)
uv venv && uv pip install -r requirements.txt
cp .env.example .env   # fill GETXAPI_KEY, OPENCODE_API_KEY, models

# 1. database (socket /tmp, port 5544)
/opt/data/pg/root/usr/lib/postgresql/17/bin/pg_ctl \
  -D /opt/data/pg/data -l /opt/data/pg/log start
export DB_URL="postgresql://urdheim@/urdheim?host=/tmp&port=5544"

# 2. read loop: backfill 3 callers -> queue -> snapshot (live DexScreener)
GETXAPI_KEY=... .venv/bin/python - <<'EOF'
from watcher.getxapi import backfill
from watcher.common import is_candidate, queue_candidate
for h in ["degenreck", "devvaintnohobby", "Tally__DE"]:
    for t in backfill(h)[0]:
        if is_candidate(t.get("text") or ""):
            queue_candidate("/tmp/q.jsonl", h, str(t["id"]), t["text"])
EOF

# 3. detective: classify each queued candidate, record real calls
OPENCODE_API_KEY=... .venv/bin/python - <<'EOF'
import json
from brain.detective import classify, record_call
for line in open("/tmp/q.jsonl"):
    item = json.loads(line)
    v = classify(item["author"], item["text"])
    if v["verdict"] == "call":
        record_call(item, v)
EOF

# 4. export rows -> dashboard data, rebuild, serve
.venv/bin/python web/export.py          # writes web-next/lib/data.js (generated)
cd web-next && npx next build && npx -y serve@latest out -l 8092
# open http://localhost:8092/leaderboard (ssh tunnel if remote)
```

`web-next/lib/data.js` is generated — the committed mock is restored
before pushing (`git checkout web-next/lib/data.js`).

## Secrets (never in repo)

`.env` holds `OPENCODE_API_KEY`, models, `DB_URL`, `TWITTERAPI_KEY`,
poster cookie path. Poster cookies mount as files (`/run/cookies-poster.json`)
via dokploy volumes; inline `POSTER_COOKIES_JSON` env is the fallback.
See `.env.example`.
