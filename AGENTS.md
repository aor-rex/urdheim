# AGENTS.md — working in this repo

## What this is

Urdheim: every memecoin call gets a receipt. Callers file calls (tag intake),
the snapshotter reprices them, receipts show peak multiple + seal
(VINDICATED / CONDEMNED / RUGGED), leaderboard ranks by median peak.
Solana + Robinhood Chain (4663). Python backend, Next.js frontend.

## Commands

```bash
./run.sh all              # api + web + poll + listen (local dev)
./run.sh snap [n]         # snapshotter one-shot
./run.sh test "@..."      # listener dry-run
```

- Local pg: socket `/tmp`, port `5544`, `DB_URL` env. See README.
- Web: `web-next/`, dev `:8092`, api `:8091`. Web reads `NEXT_PUBLIC_API`.
- Push: `git push origin main` (remote is `origin` here).

## Conventions

- Python throughout. No new deps without asking.
- Price sources: DexScreener → GeckoTerminal (solana) / onchain RPC
  (robinhood). Chain is the validator, never the text.
- Never guess an address. Below confidence: no answer, not a wrong answer.
- Receipts show peak multiple + current beside it. Leaderboard: median peak,
  never best peak.
- `.env`, `cookies.json`, `*.db`, `log/` are local-only. Never commit.
- `.env.example` = shapes only, stays tracked.
- Discord: no tables, bullets/prose only.
- UI: Lucide icons only, never emoji. Dark + warm amber/copper.

## Deploy

- `Dockerfile` (python services, CMD = `api|receiver|poll|snap|listen`)
  + `web-next/Dockerfile`. Dokploy builds both from GitHub.
- This box has no docker daemon: verify via entrypoint dry-run, not builds.
- Secrets live in Dokploy env, never in code.
