// Live API client. Pages fetch from the read API — no export step.
const BASE = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';

async function get(path) {
  const r = await fetch(BASE + path, { cache: 'no-store' });
  if (!r.ok) throw new Error(r.status + ' ' + path);
  return r.json();
}

export const apiLeaderboard = () => get('/api/leaderboard');
export const apiCaller = (h) => get('/api/caller/' + encodeURIComponent(h));
export const apiCoin = (m) => get('/api/coin/' + encodeURIComponent(m));

export const X_URL = 'https://x.com/Urdheim';

export const fmtAvg = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%';
