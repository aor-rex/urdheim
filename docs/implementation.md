# URDHEIM — full implementation (final, twitterapi.io edition)

**What:** KOL accountability engine for Solana memecoins. Callers call coins,
Urdheim snapshots the price, tracks the outcome, publishes the record.
One platform: **Urdheim**. The X poster agent is named **Heimdall**
(persona inside Urdheim, not a separate product).

**Settled decisions:**
- Language: Python throughout. FastAPI + Next.js static export for web.
- Read path: **twitterapi.io** — managed X reader, one `X-API-Key` header,
  no cookies, no shells, no ban risk, no polling. Real-time WebSocket stream
  (~250ms) replaces the entire tier-polling watcher.
- Write path: uny-x stays **only** for Heimdall posting (official X API is the
  only compliant write route — parked till revenue). Poster = separate Heimdall
  shell, never scrapes.
- Agents: plain Python scripts calling the API with `OPENCODE_API_KEY`
  (Go sub key, billed to sub). Models via `DETECT_MODEL` / `WRITER_MODEL`
  in `.env`. No opencode CLI, no login, nothing installed.
- Prices: DexScreener free API, no key.
- v1 scope: stream → brain → leaderboard + Heimdall posts. Telegram, scout,
  judge, and scale-out are later releases.

---

## Phase 0 — Foundation

- Repo `urdheim`, public from day one. VPS + Dokploy (existing). Postgres.
- `.env` (never committed): `OPENCODE_API_KEY`, `DETECT_MODEL`,
  `WRITER_MODEL`, `DB_URL`, `TWITTERAPI_KEY`, `POSTER_COOKIES`.
- Schema (4 tables):
  - `callers` — handle, uid, added_at, source (seed/snitch/scout)
  - `calls` — caller_id, coin, mint, price_at_call, mcap_at_call,
    post_url, post_id, called_at, verdict, confidence, evidence_quote
  - `snapshots` — call_id, price, mcap, liq, taken_at (nightly)
  - `submissions` — post_url, suggested_caller, status, created_at

## Phase 1 — The Stream (replaces the poll watcher)

- No reader shell, no cookies, no tiers, no polling loop. One persistent
  WebSocket (`wss://ws.twitterapi.io/twitter/tweet/stream`) with filter rules
  (`from:alice OR from:bob OR ...`, chunked ~40 handles/rule, tuned live).
  Matching tweets arrive sub-second, 24/7, all callers equal.
- Per-tweet pipeline: CA regex + call-words → match saved raw +
  DexScreener price snapshot at arrival → queue for detective.
  Non-matches discarded (~95% dies free, client-side, $0).
- Reconnect with backoff; on reconnect, gap-fill via
  `advanced_search` (`from:H since:<last_seen_id>`) so nothing is missed.
- Onboarding a new caller: `user/last_tweets` pulls recent history for
  instant backlog (fractions of a cent per caller).
- Snitch box feeds `submissions`; 3+ nominations from distinct IPs → tracked.
  Manual approval until the pattern looks honest.
- Snitch anti-abuse: nominations only queue an account for tracking — receipts
  are written solely by the detective reading real posts, so brigading can't
  fabricate a call (worst case: a clean caller gets a clean page). Every
  submission must be a real post URL containing a real call or it's binned.
  Guards: per-IP rate limit, distinct-IP rule, Cloudflare Turnstile on the box.
- Cost (100 callers, ~5 tweets/day each): ~15k tweets/mo × $0.15/1k ≈
  **~$2–3/mo**. Spending cap set in the twitterapi.io dashboard. Backfills
  are noise on top. (Old polling design would have cost ~$200/mo in requests —
  the stream is what makes this cheap.)

## Phase 2 — The Brain (API agents, unchanged)

- **Call detective** (fast model, every regex match): input post text + author
  context → output `call` / `soft-shill` / `chatting` + confidence + quoted
  evidence. Only `call` + high-confidence `soft-shill` become receipts.
- **Nightly re-pricer** (cron, no LLM): refresh price/mcap per open call,
  update caller aggregates (calls, greens, reds, avg return, worst call).
- **Report writer** (better model, daily per caller or on big moves):
  2–3 sentence verdict paragraph, stored + shown on page + reused by Heimdall.

## Phase 3 — The Web (Urdheim, unchanged)

- Public, no login, static-first (rebuild on update):
  - `/` leaderboard: ranked by score, greens/reds, worst-call preview
  - `/caller/<handle>`: every call with price-then/now, post links, verdict
  - `/coin/<mint>`: every tracked caller who touched it
  - `/snitch`: paste post link → `submissions`
- Next.js (static export) in `web-next/` — one data file renders all pages.
  Old static mockups kept in `web/` for reference.

## Phase 4 — Heimdall (poster shell, unchanged)

- Separate shell (poster never scrapes; nothing reads via cookies anymore).
- uny-x `post`, few/day max, human cadence:
  - Daily flop (worst call + receipt link) — the growth engine
  - New listing (newly tracked caller + backlog summary)
  - Rug siren (tracked-called coin rugged → original call linked, fast path)
  - Friday recap (top-3 best + worst of the week)
  - Mention replies ("is @X legit?" → scorecard link + one-liner)
- If poster flagged: stream + DB untouched, spin a new shell.
- Later: move posting to official X API (pay-per-use writes) when revenue
  covers it — the only compliant long-term write route.

## Later releases (NOT v1)

- Telegram alerts (`/follow`, `/score`) — parked till leaderboard has traction
- Caller scout (follower-graph ring detection via twitterapi.io
  `followers`/`followings` endpoints → auto-nominations)
- Dispute judge (re-read + rule with evidence log)
- Paid risk-score API

## What NEVER gets built

- No user accounts / X oauth · no onchain anything · no copy-trading,
  marketplace, or tokens · Solana only until proven

## MVP cutoff

Phases 0–3 + daily flop post. Live leaderboard with receipts, one viral
post a day. Everything after is growth.
