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
