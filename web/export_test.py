"""Exporter test: stubbed psycopg rows -> data.js shape -> node loads it.
No postgres, no key. Usage: .venv/bin/python web/export_test.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from web.export import build, render  # noqa: E402

ROWS = [
    {"handle": "rugguy", "coin": "$DUMP", "mint": "aaa",
     "chain": "solana", "price_at_call": 1.0, "called_at": "2026-09-01",
     "post_id": "1", "now_price": 0.01},      # -99%
    {"handle": "rugguy", "coin": "$DUMP2", "mint": "bbb",
     "chain": "solana", "price_at_call": 1.0, "called_at": "2026-09-02",
     "post_id": "2", "now_price": 0.02},      # -98%
    {"handle": "hoodhero", "coin": "$UP", "mint": "0xabc",
     "chain": "robinhood", "price_at_call": 1.0, "called_at": "2026-09-03",
     "post_id": "3", "now_price": 2.5},       # +150%
    {"handle": "mixed", "coin": "$A", "mint": "ccc",
     "chain": "solana", "price_at_call": 1.0, "called_at": "2026-09-04",
     "post_id": "4", "now_price": 2.0},       # +100%
    {"handle": "mixed", "coin": "$B", "mint": "0xdef",
     "chain": "robinhood", "price_at_call": 1.0, "called_at": "2026-09-05",
     "post_id": "5", "now_price": 0.5},       # -50%
]

callers = build(ROWS)
by = {c["handle"]: c for c in callers}
assert by["rugguy"]["green"] == 0 and by["rugguy"]["red"] == 2
assert by["rugguy"]["avg"] == -98 or by["rugguy"]["avg"] == -99, by["rugguy"]
assert by["hoodhero"]["chains"] == ["robinhood"], by["hoodhero"]
assert by["hoodhero"]["green"] == 1 and by["hoodhero"]["avg"] == 150
assert by["mixed"]["chains"] == ["robinhood", "solana"], by["mixed"]
assert by["mixed"]["green"] == 1 and by["mixed"]["red"] == 1
print("build: stats/chains/avg correct")

out = render(callers)
assert out.startswith("// GENERATED") and "export const callers" in out
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(out.replace("export const", "const"))
    path = f.name
print("render: header + shape OK ->", path)
print("paste this into node to verify load:",
      f"node -e \"import('{path}').then(()=>console.log('loads'))\"")
print("EXPORT PASS")
