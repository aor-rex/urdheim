'use client';
import { useEffect, useState } from 'react';
import { apiCoins, fmtMcap } from '../../lib/api';

export default function Coins() {
  const [coins, setCoins] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiCoins().then((d) => setCoins(d.coins)).catch((e) => setErr(String(e)));
  }, []);
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Tracked coins</h1>
          <div className="sub">Every coin with a filed call. Peak vs now in mcap.</div>
        </div>
        {err && <div style={{ padding: 40, color: '#c1443c' }} className="sans">api down: {err} — is ./run.sh api running?</div>}
        {!err && !coins && <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>reading the record…</div>}
        {coins && coins.length === 0 && (
          <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>
            Nothing tracked yet. Tag @urdheim on a call post and its coin lands here.</div>)}
        {(coins || []).map((c) => {
          const down = c.peak && c.now && c.now < c.peak;
          return (
            <a key={c.mint} href={'/coin/' + c.mint}
              style={{ display: 'flex', alignItems: 'center', gap: 16,
                borderBottom: '1px solid #2b2519', padding: '18px 28px',
                textDecoration: 'none', color: 'inherit' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 19 }}>
                  <span style={{ color: '#c9a227' }}>${c.coin}</span>
                  <span className="sans" style={{ fontSize: 11, color: '#5a4f35', marginLeft: 10, letterSpacing: 1 }}>{c.chain} · {c.callers} caller{c.callers === 1 ? '' : 's'}</span>
                </div>
                <div className="sans" style={{ fontSize: 12, color: '#8a7f63', marginTop: 6, wordBreak: 'break-all' }}>{c.mint}</div>
              </div>
              <div className="sans" style={{ fontSize: 12, color: '#8a7f63', textAlign: 'right', whiteSpace: 'nowrap' }}>
                <div>PEAK <b style={{ color: '#e8e0cf', fontWeight: 400 }}>{fmtMcap(c.peak)}</b></div>
                <div style={{ marginTop: 4 }}>NOW <b style={{ color: down ? '#c1443c' : '#7fb069', fontWeight: 400 }}>{fmtMcap(c.now)}</b></div>
              </div>
            </a>);
        })}
      </div>
      <aside className="siderail" />
    </>
  );
}
