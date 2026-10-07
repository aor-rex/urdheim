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
  chain         TEXT NOT NULL DEFAULT 'solana', -- solana | robinhood
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

CREATE TABLE IF NOT EXISTS poster_log (
  id         SERIAL PRIMARY KEY,
  job        TEXT NOT NULL,   -- flop | listing | siren | recap
  text       TEXT NOT NULL,
  tweet_id   TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
-- profiles: cached X identity for callers AND filers. one free user()
-- lookup at first sight, refreshed on poll. renders never wait on X.
CREATE TABLE IF NOT EXISTS profiles (
  handle     TEXT PRIMARY KEY,
  name       TEXT NOT NULL DEFAULT '',
  avatar     TEXT NOT NULL DEFAULT '',
  bio        TEXT NOT NULL DEFAULT '',
  followers  INT NOT NULL DEFAULT 0,
  following  INT NOT NULL DEFAULT 0,
  verified   BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- calls: who filed it + how hot the source post was at file time
ALTER TABLE calls ADD COLUMN IF NOT EXISTS filer_handle TEXT;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS filed_via TEXT NOT NULL DEFAULT 'seed';
ALTER TABLE calls ADD COLUMN IF NOT EXISTS likes INT NOT NULL DEFAULT 0;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS reposts INT NOT NULL DEFAULT 0;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS quotes INT NOT NULL DEFAULT 0;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS views INT NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_calls_filer ON calls(filer_handle);

-- submissions: who tagged it in
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS filer_handle TEXT;
