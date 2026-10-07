'use client';
import { use, useEffect, useState } from 'react';
import { apiCaller, fmtAvg, X_URL } from '../../../lib/api';

export default function Caller({ params }) {
  const { handle } = use(params);
  const [c, setC] = useState(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    apiCaller(handle).then(setC).catch(() => setMissing(true));
  }, [handle]);
  if (missing) return <div className="wrap" style={{ paddingTop: 60 }}>No file on @{handle} — yet. <a href="/how" style={{ color: '#c9a227' }}>File one via tag.</a></div>;
  if (!c) return <div className="wrap" style={{ paddingTop: 60, fontStyle: 'italic', color: '#8a7f63' }}>opening the file…</div>;
  const bad = c.red >= c.green;
  return (
    <div className="wrap" style={{ paddingTop: 40 }}>
      <div className="crumb"><a href="/">URDHEIM</a> &nbsp;/&nbsp; <a href="/leaderboard">LEADERBOARD</a> &nbsp;/&nbsp; @{c.handle.toUpperCase()}</div>
      <div style={{ border: '1px solid ' + (bad ? '#c1443c' : '#7fb069'), borderRadius: 4, background: bad ? '#150d0c' : '#0d140e', padding: 36, marginBottom: 20, position: 'relative' }}>
        <div className={'seal ' + (bad ? 'guilty' : 'clean')} style={{ position: 'absolute', top: 28, right: 28, transform: 'rotate(6deg)', fontSize: 12, padding: '8px 16px', borderWidth: 2, borderRadius: 6 }}>{c.seal}</div>
        <h1 style={{ fontSize: 44, fontWeight: 400 }}>@{c.handle}</h1>
        <div className="sans" style={{ fontSize: 12, color: '#8a7f63', letterSpacing: 1, marginTop: 6 }}>
          ON RECORD · {c.calls} CALLS FILED
        </div>
        <div className="sans" style={{ display: 'flex', gap: 34, margin: '26px 0', fontSize: 12, color: '#8a7f63' }}>
          <span><b className={c.green >= c.red ? 'grn' : 'rd'} style={{ display: 'block', fontSize: 28, fontFamily: 'Georgia,serif' }}>{c.green}</b>green</span>
          <span><b className="rd" style={{ display: 'block', fontSize: 28, fontFamily: 'Georgia,serif' }}>{c.red}</b>red</span>
          <span><b className={c.avg >= 0 ? 'grn' : 'rd'} style={{ display: 'block', fontSize: 28, fontFamily: 'Georgia,serif' }}>{fmtAvg(c.avg)}</b>avg return</span>
        </div>
        <div style={{ fontStyle: 'italic', fontSize: 18, lineHeight: 1.7, color: '#d6c8a8', borderLeft: '2px solid #c9a227', paddingLeft: 18 }}>{c.verdict}</div>
      </div>
      <h2 className="sans" style={{ fontSize: 13, letterSpacing: 4, color: '#c9a227', fontWeight: 400, margin: '34px 0 14px' }}>THE FULL LOG — WORST FIRST</h2>
      {c.log.map(([t, r, good]) => (
        <div key={t} className="sans" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '15px 18px', border: '1px solid #2b2519', borderRadius: 4, marginBottom: 10, background: '#121009', fontSize: 13 }}>
          <div><div style={{ fontSize: 16, color: '#f2ead6', fontWeight: 700 }}>{t}</div></div>
          <div className={good ? 'grn' : 'rd'} style={{ marginLeft: 'auto', fontWeight: 700, fontSize: 15 }}>{r}</div>
          <a href="#" style={{ color: '#c9a227', fontSize: 12 }}>receipt ↗</a>
        </div>
      ))}
      <div className="sans" style={{ display: 'flex', gap: 12, marginTop: 26 }}>
        <a href={X_URL} style={{ padding: '12px 26px', fontSize: 12, letterSpacing: 2, textDecoration: 'none', borderRadius: 3, background: '#c9a227', color: '#0c0a08', fontWeight: 700 }}>SHARE THIS FILE ON X</a>
        <a href="/how" style={{ padding: '12px 26px', fontSize: 12, letterSpacing: 2, textDecoration: 'none', borderRadius: 3, border: '1px solid #4a4132', color: '#b7a67f' }}>HOW TO FILE</a>
      </div>
    </div>
  );
}
