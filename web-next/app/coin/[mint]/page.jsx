'use client';
import { use, useEffect, useState } from 'react';
import { apiCoin, fmtMcap } from '../../../lib/api';

export default function Coin({ params }) {
  const { mint } = use(params);
  const [c, setC] = useState(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    apiCoin(mint).then(setC).catch(() => setMissing(true));
  }, [mint]);
  if (missing) return <div className="wrap" style={{ paddingTop: 60 }}>No record on this coin — yet.</div>;
  if (!c) return <div className="wrap" style={{ paddingTop: 60, fontStyle: 'italic', color: '#8a7f63' }}>reading the stone…</div>;
  const hist = (c.history || []).filter((p) => p.mcap > 0);
  const lo = hist.length ? Math.min(...hist.map((p) => p.mcap)) : 0;
  const hi = hist.length ? Math.max(...hist.map((p) => p.mcap)) : 1;
  const span = (hi - lo) || 1;
  const first = hist.length ? hist[0].mcap : 0;
  const bars = hist.length ? hist.map((p) => ({
    h: 8 + Math.round(((p.mcap - lo) / span) * 92),
    up: p.mcap >= first,
    t: p.t,
  })) : [];
  return (
    <div className="wrap coinwrap" style={{ paddingTop: 40 }}>
      <div className="crumb"><a href="/">URDHEIM</a> &nbsp;/&nbsp; COIN &nbsp;/&nbsp; {c.coin}</div>
      <div className="coingrid">
      <div style={{ border: '1px solid #2b2519', borderRadius: 4, background: '#121009', padding: '28px 22px', marginBottom: 20, maxWidth: '100%', overflow: 'hidden' }}>
        <div className="sans" style={{ fontSize: 12, color: '#5a4f35', letterSpacing: 1, wordBreak: 'break-all', lineHeight: 1.7 }}>MINT {c.mint} · {c.chain}</div>
        <h1 className="cointitle" style={{ fontWeight: 400, margin: '6px 0', overflowWrap: 'break-word' }}>${c.coin}</h1>
        <div className="sans" style={{ fontSize: 12, letterSpacing: 3, color: '#c1443c', border: '2px solid #c1443c', padding: '8px 16px', borderRadius: 6, transform: 'rotate(-3deg)', display: 'inline-block', marginTop: 10 }}>{c.dead ? 'RUGGED' : 'TRACKED'} {c.delta}</div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 170, margin: '26px 0 8px' }}>
          {bars.length === 0 && <div className="sans" style={{ fontSize: 12, color: '#5a4f35' }}>snapshots still coming in — chart fills as the watcher records.</div>}
          {bars.map((b, i) => (
            <div key={i} title={fmtMcap(hist[i].mcap) + ' · ' + hist[i].t.slice(0, 16).replace('T', ' ')} style={{ flex: 1, borderRadius: '3px 3px 0 0', minHeight: 6, height: b.h + '%',
              background: b.up ? 'linear-gradient(180deg,#7fb069,#2a4a28)' : 'linear-gradient(180deg,#c1443c,#5a1a17)' }} />
          ))}
        </div>
        <div className="sans" style={{ fontSize: 12, color: '#8a7f63', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <span>PEAK MCAP {fmtMcap(c.peak)}</span><span style={{ textAlign: 'right', flex: 1 }}>NOW MCAP {fmtMcap(c.now)}</span>
        </div>
      </div>
      <div className="coincol">
      <h2 className="sans" style={{ fontSize: 13, letterSpacing: 4, color: '#c9a227', fontWeight: 400, margin: '0 0 14px' }}>EVERY TRACKED CALLER WHO TOUCHED IT</h2>
      {c.touchers.map((t) => (
        <div key={t.handle} className="sans" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', padding: '15px 18px', border: '1px solid #2b2519', borderRadius: 4, marginBottom: 10, background: '#121009', fontSize: 13, maxWidth: '100%' }}>
          <div style={{ minWidth: 0, flex: '1 1 140px' }}><a href={'/profile/' + t.handle} style={{ fontSize: 15, color: '#f2ead6', fontWeight: 700, textDecoration: 'none' }}>@{t.handle}</a>
            <div style={{ color: '#5a4f35', fontSize: 12 }}>{t.note}</div></div>
          <div style={{ fontWeight: 700, fontSize: 12, letterSpacing: 1 }} className={t.top ? 'rd' : 'grn'}>{t.timing}</div>
          <a href={'/profile/' + t.handle} style={{ color: '#c9a227', fontSize: 12 }}>receipt ↗</a>
        </div>
      ))}
      <p style={{ fontStyle: 'italic', color: '#9a8c6c', marginTop: 22, lineHeight: 1.7 }}>{c.note}</p>
      </div>
      </div>
    </div>
  );
}
