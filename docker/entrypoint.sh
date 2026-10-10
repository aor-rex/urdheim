#!/usr/bin/env bash
# Service dispatcher. CMD is one of: api | receiver | poll | snap | listen.
set -u
cd /app

apply_schema() {
  python -c "
import os, psycopg
db = os.environ['DB_URL']
with psycopg.connect(db) as c, c.cursor() as cur:
    cur.execute(open('/app/schema.sql').read())
    cur.execute(open('/app/migrate.sql').read())
    c.commit()
print('schema: ok')"
}

case "${1:-api}" in
  api)
    apply_schema
    exec python -m uvicorn api.server:app --host 0.0.0.0 --port 8091
    ;;
  receiver)
    exec python -m uvicorn receiver.hook:app --host 0.0.0.0 --port 8091
    ;;
  poll)
    # backfill + classify + snitch, every POLL_EVERY (default 10 min)
    while true; do
      python - <<'EOF'
from watcher.getxapi import backfill
from watcher.common import is_candidate, queue_candidate
from listener.mentions import load_seeds
from brain.detective import classify, record_call
from brain.budget import BudgetStop
import json, os
donep = os.environ.get("DONE_PATH", "/tmp/q.done")
qp = os.environ.get("QUEUE_PATH", "/tmp/q.jsonl")
done = set(open(donep).read().split()) if os.path.exists(donep) else set()
with open(donep, "a") as df:
    for h in load_seeds():
        try:
            tweets = backfill(h)[0]
        except BudgetStop as e:
            print(f"poll stop @{h}: {e} (sleeping till next round)", flush=True)
            break
        except Exception as e:
            print(f"poll skip @{h}: {str(e)[:120]}", flush=True)
            continue
        for t in tweets:
            if not is_candidate(t.get("text") or ""):
                continue
            queue_candidate(qp, h, str(t["id"]), t["text"] or "")
    for line in open(qp):
        item = json.loads(line)
        pid = str(item.get("post_id"))
        if pid in done:
            continue
        done.add(pid)
        df.write(pid + "\n"); df.flush()
        try:
            v = classify(item["author"], item["text"])
        except BudgetStop as e:
            print(f"classify stop: {e} (sleeping till next round)", flush=True)
            break
        except Exception as e:
            print(f"classify skip {pid}: {str(e)[:120]}", flush=True)
            continue
        print(item["author"], (item.get("mint") or "")[:14], "->", v["verdict"], flush=True)
        if v["verdict"] == "call":
            try:
                record_call(item, v)
            except Exception as e:
                print(f"record skip {pid}: {str(e)[:120]}", flush=True)
print("poll done", flush=True)
EOF
      python brain/snitch_worker.py --limit 20
      sleep "${POLL_EVERY:-600}"
    done
    ;;
  snap)
    # reprice open calls, every SNAP_EVERY (default 15 min)
    while true; do
      python brain/snapshotter.py "${SNAP_LIMIT:-200}"
      # milestone quotes: dry unless WRITE_LIVE=1
      if [ "${WRITE_LIVE:-0}" = "1" ]; then FLAGS="--live --allow"; else FLAGS=""; fi
      python listener/milestones.py $FLAGS
      # weekly board: fridays only (script skips empty weeks itself)
      [ "$(date -u +%u)" = 5 ] && python listener/weekly.py $FLAGS || true
      sleep "${SNAP_EVERY:-900}"
    done
    ;;
  listen)
    while true; do
      python -u listener/mentions.py --once 2>&1
      # ask-confirm expiries: silence is never a position (cheap, idempotent)
      python listener/askconfirm.py 2>&1 | tail -1
      sleep 60
    done
    ;;
  *)
    echo "usage: api | receiver | poll | snap | listen"; exit 1 ;;
esac
