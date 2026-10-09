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
  const bars = [100, 88, 70, 44, 26, 14, 8, 16, 5, 3];
  return (
    <div className="wrap" style={{ paddingTop: 40 }}>
      <div className="crumb"><a href="/">URDHEIM</a> &nbsp;/&nbsp; COIN &nbsp;/&nbsp; {c.coin}</div>
      <div style={{ border: '1px solid #2b2519', borderRadius: 4, background: '#121009', padding: '28px 22px', marginBottom: 20, maxWidth: '100%', overflow: 'hidden' }}>
        <div className="sans" style={{ fontSize: 12, color: '#5a4f35', letterSpacing: 1, wordBreak: 'break-all', lineHeight: 1.7 }}>MINT {c.mint} · {c.chain}</div>
        <h1 style={{ fontSize: 'clamp(30px, 8vw, 48px)', fontWeight: 400, margin: '6px 0', overflowWrap: 'break-word' }}>{c.coin}</h1>
        <div className="sans" style={{ fontSize: 12, letterSpacing: 3, color: '#c1443c', border: '2px solid #c1443c', padding: '8px 16px', borderRadius: 6, transform: 'rotate(-3deg)', display: 'inline-block', marginTop: 10 }}>{c.dead ? 'RUGGED' : 'TRACKED'} {c.delta}</div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 130, margin: '26px 0 8px' }}>
          {bars.map((h, i) => (
            <div key={i} style={{ flex: 1, borderRadius: '3px 3px 0 0', minHeight: 6, height: h + '%',
              background: h === 16 ? 'linear-gradient(180deg,#7fb069,#2a4a28)' : 'linear-gradient(180deg,#c1443c,#5a1a17)' }} />
          ))}
        </div>
        <div className="sans" style={{ fontSize: 12, color: '#8a7f63', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <span>PEAK MCAP {fmtMcap(c.peak)}</span><span style={{ textAlign: 'right', flex: 1 }}>NOW MCAP {fmtMcap(c.now)}</span>
        </div>
      </div>
      <h2 className="sans" style={{ fontSize: 13, letterSpacing: 4, color: '#c9a227', fontWeight: 400, margin: '34px 0 14px' }}>EVERY TRACKED CALLER WHO TOUCHED IT</h2>
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
  );
}
