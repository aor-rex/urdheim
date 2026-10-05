"""Urdheim fixture e2e: fake WS server -> stream_loop -> queue.jsonl.
No twitterapi key, no postgres. DexScreener snapshot runs LIVE (free).
Usage: .venv/bin/python tests/e2e_fixture.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "watcher"))

SUNUSI = "2vvw3cSwibzGD6SgW9QzRaBdmjkYrvs218DUy6VWpump"

FIXTURES = [
    {"id": "9001", "screen_name": "testcaller",
     "text": f"apeing {SUNUSI} here, this is the entry. send it 100x"},
    {"id": "9002", "screen_name": "talkguy",
     "text": "solana fees are so low today, lovely weather for Henrys"},
    {"id": "9003", "screen_name": "softshill",
     "text": f"not saying buy, just observing {SUNUSI} looks interesting"},
]


async def fake_server(stop):
    import websockets

    async def handler(ws):
        for tw in FIXTURES:
            await ws.send(json.dumps(tw))
            await asyncio.sleep(0.2)
        await stop.wait()

    async with websockets.serve(handler, "127.0.0.1", 8765):
        await stop.wait()


async def main():
    import watch

    qpath = "/tmp/urdheim-test-queue.jsonl"
    if os.path.exists(qpath):
        os.remove(qpath)
    os.environ["TWITTERAPI_KEY"] = "dummy"
    os.environ["TWITTERAPI_WS"] = "ws://127.0.0.1:8765"
    os.environ["QUEUE_PATH"] = qpath
    # re-read env (module captured WS at import; override directly)
    watch.WS = os.environ["TWITTERAPI_WS"]

    stop = asyncio.Event()
    server = asyncio.create_task(fake_server(stop))
    await asyncio.sleep(0.3)
    stream = asyncio.create_task(watch.stream_loop(qpath))
    await asyncio.sleep(2.5)
    stream.cancel()
    stop.set()
    try:
        await stream
    except asyncio.CancelledError:
        pass
    await server

    queued = [json.loads(l) for l in open(qpath)]
    print(f"queued: {len(queued)}")
    for q in queued:
        snap = q.get("snapshot") or {}
        print(f"  @{q['author']} {q['post_id']} mint={q['mint'][:8]}… "
              f"price={snap.get('price')} mcap={snap.get('mcap')}")
    ids = {q["post_id"] for q in queued}
    assert "9001" in ids, "real call missing!"
    assert "9003" in ids, "CA-bearing post missing!"
    assert "9002" not in ids, "chatter leaked through!"
    assert all((q.get("snapshot") or {}).get("price") for q in queued), \
        "snapshot missing!"
    print("E2E FIXTURE PASS: 2 queued (9001, 9003), 1 discarded (9002), "
          "live snapshots attached")


asyncio.run(main())
