# URDHEIM — full implementation (final)

**What:** KOL accountability engine for Solana memecoins. Callers call coins,
Urdheim snapshots the price, tracks the outcome, publishes the record.
One platform: **Urdheim**. The X poster agent is named **Heimdall**
(persona inside Urdheim, not a separate product).

**Settled decisions:**
- Language: Python throughout (watcher IS uny-x; agents import it directly;
  FastAPI + static HTML for web).
- Agents: plain Python scripts calling the API with `OPENCODE_API_KEY`
  (Go sub key, billed to sub). Models via `DETECT_MODEL` / `WRITER_MODEL`
  in `.env`. No opencode CLI, no login, nothing installed.
- Watcher auth: shell reader account cookies (`cookies-watcher.json`,
  gitignored, ~3-month life). Polling delay accepted.
- Prices: DexScreener free API, no key.
- v1 scope: watcher → brain → leaderboard + Heimdall posts. Telegram, scout,
  judge, and scale-out are later releases.

---

## Phase 0 — Foundation

- Repo `urdheim`, public from day one. VPS + Dokploy (existing). Postgres.
- `.env` (never committed): `OPENCODE_API_KEY`, `DETECT_MODEL`,
  `WRITER_MODEL`, `DB_URL`, `WATCHER_COOKIES`, `POSTER_COOKIES`.
- Schema (4 tables):
  - `callers` — handle, uid, added_at, source (seed/snitch/scout), tier
  - `calls` — caller_id, coin, mint, price_at_call, mcap_at_call,
    post_url, post_id, called_at, verdict, confidence, evidence_quote
  - `snapshots` — call_id, price, mcap, liq, taken_at (nightly)
  - `submissions` — post_url, suggested_caller, status, created_at

## Phase 1 — The Watcher (reader shell)

- Reader = existing @ryu_ngmi session (owner accepted the blast-radius risk).
  Poster = separate Heimdall shell, never scrapes. Cookies on server.
- Seed 50–100 Solana callers, tiered:
  - Tier 1 (~20 by reach): poll every 2–5 min
  - Tier 2 (rest): poll every 15–30 min
- Per-post pipeline: regex (Solana CA pattern + call-words) → match saved raw
  + DexScreener price snapshot at detection minute → queue for detective.
  Non-matches discarded (~95% dies free).
- Cursor loop-guards everywhere (seen-set, break on repeat).
- Snitch box feeds `submissions`; 3+ nominations from distinct IPs → auto Tier 3.
  Manual approval until the pattern looks honest.
- Snitch anti-abuse: nominations only queue an account for tracking — receipts
  are written solely by the detective reading real posts, so brigading can't
  fabricate a call (worst case: a clean caller gets a clean page). Every
  submission must be a real post URL containing a real call or it's binned.
  Guards: per-IP rate limit, distinct-IP rule, Cloudflare Turnstile on the box.

## Phase 2 — The Brain (API agents)

- **Call detective** (fast model, every regex match): input post text + author
  context → output `call` / `soft-shill` / `chatting` + confidence + quoted
  evidence. Only `call` + high-confidence `soft-shill` become receipts.
- **Nightly re-pricer** (cron, no LLM): refresh price/mcap per open call,
  update caller aggregates (calls, greens, reds, avg return, worst call).
- **Report writer** (better model, daily per caller or on big moves):
  2–3 sentence verdict paragraph, stored + shown on page + reused by Heimdall.

## Phase 3 — The Web (Urdheim)

- Public, no login, static-first (rebuild on update):
  - `/` leaderboard: ranked by score, greens/reds, worst-call preview
  - `/caller/<handle>`: every call with price-then/now, post links, verdict
  - `/coin/<mint>`: every tracked caller who touched it
  - `/snitch`: paste post link → `submissions`
- Next.js (static export) in `web-next/` — one data file renders all pages.
  Old static mockups kept in `web/` for reference.

## Phase 4 — Heimdall (poster shell)

- Separate shell from reader (reader never posts; poster never scrapes).
- uny-x `post`, few/day max, human cadence:
  - Daily flop (worst call + receipt link) — the growth engine
  - New listing (newly tracked caller + backlog summary)
  - Rug siren (tracked-called coin rugged → original call linked, fast path)
  - Friday recap (top-3 best + worst of the week)
  - Mention replies ("is @X legit?" → scorecard link + one-liner)
- If poster flagged: reader + DB untouched, spin a new shell.

## Later releases (NOT v1)

- Telegram alerts (`/follow`, `/score`) — parked till leaderboard has traction
- Caller scout (coordinated-ring detection → auto-nominations)
- Dispute judge (re-read + rule with evidence log)
- Scale-out (split caller list across 2–3 readers), paid risk-score API

## What NEVER gets built

- No user accounts / X oauth · no onchain anything · no copy-trading,
  marketplace, or tokens · Solana only until proven

## MVP cutoff

Phases 0–3 + daily flop post. Live leaderboard with receipts, one viral
post a day. Everything after is growth.
