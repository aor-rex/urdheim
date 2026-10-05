# Urdheim — KOL accountability engine for Solana memecoins.

Every call leaves a record. `docs/implementation.md` is the source of truth.

## Layout

- `docs/implementation.md` — full plan (phases, decisions, MVP cutoff)
- `schema.sql` — postgres: callers, calls, snapshots, submissions
- `watcher/` — stream watcher: twitterapi.io filter stream, regex CAs, snapshot price, queue
- `brain/` — detective (API verdicts), repricer + writer land here next
- `web/` — leaderboard + pages land here (phase 3)

## Quickstart (no secrets needed)

```bash
cp .env.example .env
psql $DB_URL -f schema.sql
python3 watcher/watch.py   # needs TWITTERAPI_KEY + watcher/seed.json; backfills then streams
```

## Secrets (never in repo)

`.env` holds `OPENCODE_API_KEY`, models, `DB_URL`, `TWITTERAPI_KEY`,
poster cookie path. Poster cookies mount as files (`/run/cookies-poster.json`)
via dokploy volumes; inline `POSTER_COOKIES_JSON` env is the fallback.
See `.env.example`.
