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
import os
qp = "/tmp/q.jsonl"
donep = "/tmp/q.done"
queued = set()
try:
    queued = {json.loads(l).get("post_id") for l in open(qp)}
except Exception:
    pass
done = set(open(donep).read().split()) if os.path.exists(donep) else set()
n_q = 0
for h in load_seeds():
    for t in backfill(h)[0]:
        if str(t["id"]) in queued:
            continue
        if is_candidate(t.get("text") or ""):
            queue_candidate(qp, h, str(t["id"]), t["text"] or "")
            n_q += 1
n_r = 0
with open(donep, "a") as df:
    for line in open(qp):
        item = json.loads(line)
        pid = str(item.get("post_id"))
        if pid in done:
            continue
        done.add(pid)
        v = classify(item["author"], item["text"])
        df.write(pid + "\n"); df.flush()
    print(item["author"], item["mint"][:14], "->", v["verdict"], v["confidence"], flush=True)
    if v["verdict"] == "call":
        record_call(item, v); n_r += 1
print(f"poll done: queued={n_q} recorded={n_r}", flush=True)
EOF
  tail -3 "$ROOT/log/poll.log"
  echo "[$(date +%H:%M:%S)] poll: processing snitch submissions"
  "$ROOT/.venv/bin/python" "$ROOT/brain/snitch_worker.py" --limit 20 \
    2>&1 | tee -a "$ROOT/log/snitch.log" | tail -2
}

cmd_api() {
  echo "api: http://localhost:8091/api/leaderboard (logs: $ROOT/log/api.log, ctrl-c to stop)"
  (cd "$ROOT" && ./.venv/bin/python -m uvicorn api.server:app --port 8091 \
    >"$ROOT/log/api.log" 2>&1 &)
  sleep 3
  tail -3 "$ROOT/log/api.log"
  curl -s http://localhost:8091/api/stats || echo "api not up — check $ROOT/log/api.log"
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

cmd_test() {
  "$ROOT/.venv/bin/python" "$ROOT/listener/mentions.py" --dry "--test=$1"
}

cmd_snitch() {
  echo "snitch worker: processing pending submissions (logs: $ROOT/log/snitch.log)"
  "$ROOT/.venv/bin/python" "$ROOT/brain/snitch_worker.py" --limit "${1:-20}" \
    2>&1 | tee -a "$ROOT/log/snitch.log" | tail -3
}

case "${1:-}" in
  poll)   pg_ok && cmd_poll ;;
  api)    pg_ok && cmd_api ;;
  dev)    cmd_dev ;;
  listen) cmd_listen "${2:-}" ;;
  test)   cmd_test "${2:-@urdheim check 0x008Df4b3E857D06c4603Aeb11F267ccD32ce2005}" ;;
  snitch) pg_ok && cmd_snitch "${2:-20}" ;;
  all)    pg_ok && cmd_api && cmd_dev && cmd_poll && cmd_listen ;;
  *) echo "usage: ./run.sh poll | api | dev | listen [--dry] | test \"@urdheim ...\" | snitch [n] | all"; exit 1 ;;
esac
