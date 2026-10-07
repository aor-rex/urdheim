#!/usr/bin/env bash
# urdheim local runner — ./run.sh dev | poll | listen | all
# needs: .env filled, postgres started (see README local run).
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/log"
set -a; source "$ROOT/.env" 2>/dev/null || true; set +a

pg_ok() {
  "$ROOT/.venv/bin/python" -c "
import os, psycopg
psycopg.connect(os.environ['DB_URL']).close()
print('db: up')" 2>&1 | tail -1
}

cmd_poll() {
  echo "[$(date +%H:%M:%S)] poll: backfill -> classify -> record"
  "$ROOT/.venv/bin/python" - >>"$ROOT/log/poll.log" 2>&1 <<'EOF'
from watcher.getxapi import backfill
from watcher.common import is_candidate, queue_candidate
from listener.mentions import load_seeds
from brain.detective import classify, record_call
import json
qp = "/tmp/q.jsonl"
n_q = 0
for h in load_seeds():
    for t in backfill(h)[0]:
        if is_candidate(t.get("text") or ""):
            queue_candidate(qp, h, str(t["id"]), t["text"] or "")
            n_q += 1
n_r = 0
for line in open(qp):
    item = json.loads(line)
    v = classify(item["author"], item["text"])
    print(item["author"], item["mint"][:14], "->", v["verdict"], v["confidence"], flush=True)
    if v["verdict"] == "call":
        record_call(item, v); n_r += 1
print(f"poll done: queued={n_q} recorded={n_r}", flush=True)
EOF
  tail -3 "$ROOT/log/poll.log"
  echo "[$(date +%H:%M:%S)] poll: exporting dashboard data"
  DB_URL="$DB_URL" "$ROOT/.venv/bin/python" "$ROOT/web/export.py"
}

cmd_dev() {
  echo "dev server: http://localhost:8092/leaderboard (ctrl-c to stop)"
  echo "logs: tail -f $ROOT/log/dev.log"
  (cd "$ROOT/web-next" && npx next dev -p 8092 >"$ROOT/log/dev.log" 2>&1 &) 
  sleep 4
  tail -5 "$ROOT/log/dev.log"
}

cmd_listen() {
  local dry="${1:-}"
  echo "listener: polling mentions every 60s (logs: $ROOT/log/listen.log, ctrl-c to stop)"
  while true; do
    "$ROOT/.venv/bin/python" "$ROOT/listener/mentions.py" --once $dry \
      >>"$ROOT/log/listen.log" 2>&1
    tail -2 "$ROOT/log/listen.log"
    sleep 60
  done
}

case "${1:-}" in
  poll)   pg_ok && cmd_poll ;;
  dev)    cmd_dev ;;
  listen) cmd_listen "${2:-}" ;;
  all)    pg_ok && cmd_poll && cmd_dev && cmd_listen ;;
  *) echo "usage: ./run.sh poll | dev | listen [--dry] | all"; exit 1 ;;
esac
