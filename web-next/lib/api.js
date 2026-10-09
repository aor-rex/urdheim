// Live API client. Pages fetch from the read API — no export step.
export const API_BASE = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';
const BASE = API_BASE;

// Identity, fetched once per session then shared. Every component that
// needs the signed-in user goes through here — never a fresh /me per mount.
let _me = null;
let _meAt = 0;
const ME_TTL = 5 * 60 * 1000;

export async function fetchMe() {
  const now = Date.now();
  if (_me && now - _meAt < ME_TTL) return _me;
  try {
    const m = await fetch(API_BASE + '/api/auth/me',
      { credentials: 'include', cache: 'no-store' }).then(r => r.json());
    if (!m.handle) {
      _me = { handle: null, profile: null };
    } else {
      const p = await fetch(API_BASE + '/api/profile/' +
        encodeURIComponent(m.handle), { cache: 'no-store' }).then(r => r.json());
      _me = { handle: m.handle, profile: p.profile || null };
    }
  } catch (e) {
    _me = { handle: null, profile: null };
  }
  _meAt = Date.now();
  return _me;
}

// Sign out everywhere: server clears the session cookie, local cache drops.
export async function signOut() {
  try {
    await fetch(API_BASE + '/api/auth/logout',
      { method: 'POST', credentials: 'include' });
  } catch (e) { /* offline: clear locally anyway */ }
  document.cookie = 'urdheim_sess=; Max-Age=0; path=/; Secure; SameSite=Lax';
  _me = { handle: null, profile: null };
  _meAt = Date.now();
}

async function get(path) {
  const r = await fetch(BASE + path, { cache: 'no-store' });
  if (!r.ok) throw new Error(r.status + ' ' + path);
  return r.json();
}

export const apiLeaderboard = () => get('/api/leaderboard');
export const apiCaller = (h) => get('/api/caller/' + encodeURIComponent(h));
export const apiCoin = (m) => get('/api/coin/' + encodeURIComponent(m));
export const apiFeed = (n) => get('/api/feed?limit=' + (n || 30));
export const apiProfile = (h) => get('/api/profile/' + encodeURIComponent(h));
export const apiStats = () => get('/api/stats');

export const X_URL = 'https://x.com/Urdheim';

export const fmtAvg = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%';

// X serves _normal (48px). Swap to _400x400 for crisp renders.
export const avatar = (url) => (!url ? '' : url.replace('_normal.', '_400x400.'));

export const fmtCount = (n) => {
  n = n || 0;
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace('.0', '') + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1).replace('.0', '') + 'K';
  return String(n);
};

export const fmtMcap = (n) => {
  if (n === null || n === undefined) return '—';
  if (n >= 1000000000) return '$' + (n / 1000000000).toFixed(2) + 'B';
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(2) + 'M';
  if (n >= 1000) return '$' + (n / 1000).toFixed(1).replace('.0', '') + 'K';
  return '$' + String(Math.round(n));
};

export const timeAgo = (ts) => {
  const t = new Date(ts).getTime();
  if (isNaN(t)) return '';
  const s = Math.max(1, Math.floor((Date.now() - t) / 1000));
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  if (s < 86400) return Math.floor(s / 3600) + 'h ago';
  return Math.floor(s / 86400) + 'd ago';
};

export const fmtPrice = (p) => {
  if (p === null || p === undefined) return null;
  if (p === 0) return '$0';
  if (p < 0.01) return '$' + p.toPrecision(3);
  return '$' + Number(p).toLocaleString(undefined, { maximumFractionDigits: 4 });
};
