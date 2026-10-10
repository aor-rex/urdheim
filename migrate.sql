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

-- tag allowlist: only signed-in handles get @urdheim responses.
-- strangers get one signin nudge, then silence (protects the 7/day cap).
CREATE TABLE IF NOT EXISTS allowed_users (
  handle   TEXT PRIMARY KEY,
  x_id     TEXT,
  nudged   BOOLEAN NOT NULL DEFAULT FALSE,
  added_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE allowed_users ADD COLUMN IF NOT EXISTS refresh_token TEXT NOT NULL DEFAULT '';
-- no json file: add/remove handles without touching the repo.
CREATE TABLE IF NOT EXISTS watched (
  handle   TEXT PRIMARY KEY,
  source   TEXT NOT NULL DEFAULT 'seed',   -- seed | enroll | snitch
  active   BOOLEAN NOT NULL DEFAULT TRUE,
  added_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO watched (handle, source) VALUES
  ('degenreck', 'seed'),
  ('devvaintnohobby', 'seed'),
  ('Tally__DE', 'seed')
ON CONFLICT (handle) DO NOTHING;
-- peak_x decides receipts + leaderboard (median, never best). state decides seals.
ALTER TABLE calls ADD COLUMN IF NOT EXISTS peak DOUBLE PRECISION;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS peak_at TIMESTAMPTZ;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS peak_x DOUBLE PRECISION;
-- milestone quotes: one quote-tweet per threshold, never repeated.
ALTER TABLE calls ADD COLUMN IF NOT EXISTS hit_3x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS hit_5x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS hit_10x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS quoted_3x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS quoted_5x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS quoted_10x BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT 'open';
CREATE INDEX IF NOT EXISTS idx_calls_state ON calls(state);

-- dual receipts: caller backdated to post time, filer stamped at tag time.
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS caller_post_ts TIMESTAMPTZ;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS tag_post_id TEXT NOT NULL DEFAULT '';
ALTER TABLE calls ADD COLUMN IF NOT EXISTS entry_estimated BOOLEAN NOT NULL DEFAULT FALSE;
CREATE TABLE IF NOT EXISTS filer_entries (
  id            SERIAL PRIMARY KEY,
  call_id       INT REFERENCES calls(id),
  caller_handle TEXT NOT NULL,
  mint          TEXT NOT NULL,
  filer_handle  TEXT NOT NULL,
  price_at_tag  DOUBLE PRECISION,
  mcap_at_tag   DOUBLE PRECISION,
  tag_post_id   TEXT NOT NULL DEFAULT '',
  created_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE (filer_handle, tag_post_id)
);
CREATE INDEX IF NOT EXISTS idx_filer_entries_filer ON filer_entries(filer_handle);
