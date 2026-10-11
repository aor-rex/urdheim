# Urdheim — every memecoin call gets a receipt.

Tag `@Urdheim track this <mint>` on X and the call is filed, repriced
against onchain history, and served as a receipt: entry, peak
multiple, seal (VINDICATED / RUGGED / CONDEMNED). Leaderboard ranks by
median peak, never best peak. Solana + Robinhood Chain.
Live at https://urdheim.zone.id.

## How it works

- Tag intake: a mention files a receipt, stamped at tag time.
- Snapshotter reprices open calls on a loop (DexScreener + onchain
  history, including backdated entries).
- Milestones (3x / 5x / 10x) and a Friday board post go out from the
  account. Soft mentions stay unconfirmed until volume agrees — a
  wrong address never ships.
- Feed, board, coins, stats, profiles: Next.js frontend + Python API.

## Layout

- `api/` — API + auth.
- `web-next/` — frontend.
- `listener/` — mentions, posting lanes.
- `watcher/` — polling, pricing, history.
- `brain/` — classification, derivation, spend gates.
- `poster/` — post transport. `receiver/` — webhook intake.
- `tests/` — suites + dry-run simulator.

## Local dev

```bash
./run.sh all              # api + web + poll + listen
./run.sh snap [n]         # snapshotter one-shot
./run.sh test "@..."      # listener dry-run
.venv/bin/python tests/simulate.py   # dry story, 0 tweets
```

Local pg over `/tmp` socket, `DB_URL` env. Copy `.env.example` to
`.env` — shapes only in the repo, values never.
