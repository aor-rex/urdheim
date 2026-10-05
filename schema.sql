CREATE TABLE IF NOT EXISTS callers (
  id          SERIAL PRIMARY KEY,
  handle      TEXT UNIQUE NOT NULL,
  uid         TEXT,
  added_at    TIMESTAMPTZ DEFAULT now(),
  source      TEXT NOT NULL DEFAULT 'seed'    -- seed | snitch | scout
  -- no tiers: the stream covers every caller in real time, equally
);

CREATE TABLE IF NOT EXISTS calls (
  id            SERIAL PRIMARY KEY,
  caller_id     INT REFERENCES callers(id),
  coin          TEXT NOT NULL,
  mint          TEXT NOT NULL,
  price_at_call DOUBLE PRECISION,
  mcap_at_call  DOUBLE PRECISION,
  post_url      TEXT UNIQUE NOT NULL,
  post_id       TEXT UNIQUE NOT NULL,
  called_at     TIMESTAMPTZ,
  verdict       TEXT,                          -- call | soft-shill | chatting
  confidence    DOUBLE PRECISION,
  evidence_quote TEXT
);

CREATE TABLE IF NOT EXISTS snapshots (
  id        SERIAL PRIMARY KEY,
  call_id   INT REFERENCES calls(id),
  price     DOUBLE PRECISION,
  mcap      DOUBLE PRECISION,
  liq       DOUBLE PRECISION,
  taken_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_snapshots_call ON snapshots(call_id, taken_at);

CREATE TABLE IF NOT EXISTS submissions (
  id               SERIAL PRIMARY KEY,
  post_url         TEXT NOT NULL,
  suggested_caller TEXT,
  reporter_ip      TEXT,
  status           TEXT NOT NULL DEFAULT 'pending',  -- pending|accepted|rejected
  created_at       TIMESTAMPTZ DEFAULT now()
);
