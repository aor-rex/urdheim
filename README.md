# Urdheim — every memecoin call gets a receipt.

Callers get tagged on X. Urdheim files the call, reprices it against
onchain history, and serves the receipt: entry, peak multiple, seal
(VINDICATED / RUGGED / CONDEMNED). Leaderboard ranks by median peak,
never best peak. Solana + Robinhood Chain. Live at
https://urdheim.zone.id (apex only, no subdomains).

## The loop

**Read (always on).**

- Tag intake: `@Urdheim track this <mint>` → listener files a receipt,
  stamped at tag time ("seen at $X mc"). Chain is the validator, never
  the text — below confidence: no answer, not a wrong answer.
- Poller backfills seed callers every 10 min (GetXAPI `user/tweets`).
- Snapshotter reprices open calls every 15 min (DexScreener → Solana
  history / Robinhood Sync logs for backdated entries).
- Feed, board, coins, stats, profiles: Next.js on `web-next/`, API on
  `api/server.py`. Server TTL cache (30s feed/board/stats, 60s
  profiles), client warm cache on top.

**Write (dry by default, `WRITE_LIVE=1` arms it).**

- Ask-confirm: `@Urdheim did you get in?` (100-like gate) → asker gets
  a consent reply; yes = receipt, silence = interest only, 7-day expiry.
- Milestones: 3x / 5x / 10x crossings quoted once each, tracked-only.
- Weekly: Friday top-3 board post.
- Hints / derivation: soft-shill CAs stay `proposed` until volume
  confirms. A wrong CA is unrecoverable — unknown never ships.
- All sends go through `listener/outbox.py` (GetXAPI, 7/day budget +
  25/day cap, every send to `spend.jsonl`). Failures never mark sent —
  retried next round.
- Replies carry no external links: X ghost-filters link replies from
  young accounts (reply_count rises, nothing renders). Receipt link
  lives in the bio; reply text rotates so repeats skip the
  duplicate-text filter.

## Services (one image, CMD picks the service)

- `api` — OAuth (X, PKCE), feed/board/coin/stats, `POST /api/ops`
  (stealth admin for the operator handle: capability HMAC, boring verb
  names, identical error shape, no public route).
- `web` — Next.js frontend.
- `receiver` — GetXAPI webhook at `/hook` (fail-safe 401 without secret;
  poller covers gaps).
- `poll` — seed backfill loop.
- `snap` — snapshotter + milestones + Friday weekly.
- `listen` — mentions + ask expiry.

`docker/entrypoint.sh` runs the loops. `WRITE_LIVE` empty = dry.
Service shims in `Dockerfile` (`/usr/local/bin/{api,receiver,poll,
snap,listen}`) so the app command resolves whether or not the
entrypoint slot survives a deploy.

## Brain

- `brain/intent.py` — what the mention wants. `brain/detective.py` —
  model verdicts (opencode-go, same model throughout).
- `brain/derive.py` — text → dHash → vision → crowd. Crowd confirms,
  never overrules. Vision (`VISION_MODEL`) returns None keyless, never
  guesses.
- `brain/budget.py` — per-endpoint spend gates; everything billable
  goes through `allow`/`log`.

## Local dev

```bash
./run.sh all              # api + web + poll + listen
./run.sh snap [n]         # snapshotter one-shot
./run.sh test "@..."      # listener dry-run
.venv/bin/python tests/simulate.py   # 7-act dry story, 0 tweets
```

Full suite: `test_outbox` 6/6, `test_milestones`, `test_weekly`,
`test_askconfirm`, `test_derive`, `test_hints` — all green via
`.venv/bin/python` (system python lacks deps).

Local pg: socket `/tmp`, port `5544`, `DB_URL` env. This box has no
docker daemon — verify via dry-runs, dokploy builds are truth.

## Deploy

Dokploy, GitHub push → webhook rebuild. Apex-only routing
(`urdheim.zone.id/api`, `/hook`). Secrets live in dokploy env, never
in code: `.env.example` = shapes only, stays tracked. Cookies move via
cookie-editor JSON exports, never passwords.

## Conventions

- Python throughout. No new deps without asking.
- Never guess an address. Wrong CA stays `proposed`.
- Receipts: peak multiple beside current. Board: median peak.
- UI: Lucide icons, never emoji. Dark + warm amber/copper `#c9a227`.
- Chat surfaces (Discord): bullets/prose, never tables.
