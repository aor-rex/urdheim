# Urdheim — KOL accountability engine for Solana memecoins.

Every call leaves a record. `docs/implementation.md` is the source of truth.

## Layout

- `docs/implementation.md` — full plan (phases, decisions, MVP cutoff)
- `schema.sql` — postgres: callers, calls, snapshots, submissions
- `watcher/` — reader loop: poll callers, regex CAs, snapshot price, queue
- `brain/` — detective (API verdicts), repricer + writer land here next
- `web/` — leaderboard + pages land here (phase 3)

## Quickstart (no secrets needed)

```bash
cp .env.example .env
psql $DB_URL -f schema.sql
python3 watcher/watch.py   # validates pipeline; live polling needs WATCHER_COOKIES
```

## Secrets (never in repo)

`.env` holds `OPENCODE_API_KEY`, models, `DB_URL`, cookie paths.
Cookies mount as files (`/run/cookies-*.json`) via dokploy volumes;
inline `*_JSON` env is the fallback. See `.env.example`.
