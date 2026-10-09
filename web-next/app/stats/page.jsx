'use client';
import { useEffect, useState } from 'react';
import { apiStats } from '../../lib/api';
import { RailBox, RailRow, SignInBox, Scale, TrendingUp } from '../../lib/components';

function Num({ v, label, color }) {
  return (
    <div style={{ flex: '1 1 140px', textAlign: 'center', padding: '20px 8px',
      borderRight: '1px solid #2b2519' }}>
      <div style={{ fontSize: 30, color: color || '#e8e0cf' }}>{v}</div>
      <div className="sans" style={{ fontSize: 11, letterSpacing: 2, color: '#5a4f35', marginTop: 6 }}>{label}</div>
    </div>);
}

export default function Stats() {
  const [s, setS] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiStats().then(setS).catch((e) => setErr(String(e)));
  }, []);
  const st = (s && s.states) || {};
  const total = (s && s.calls) || 0;
  const bar = (n) => (total ? Math.round((n / total) * 100) : 0);
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Stats</h1>
          <div className="sub">The ledger so far. Every number below reads live from the record.</div>
        </div>
        {err && <div style={{ padding: 40, color: '#c1443c' }} className="sans">api down: {err}</div>}
        {!err && !s && <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>counting the receipts…</div>}
        {s && (<>
          <div className="sans" style={{ display: 'flex', flexWrap: 'wrap', borderBottom: '1px solid #2b2519' }}>
            <Num v={s.calls} label="CALLS FILED" />
            <Num v={s.callers} label="CALLERS TRACKED" />
            <Num v={s.snapshots} label="SNAPSHOTS" />
            <Num v={s.scored} label="SCORED" />
          </div>
          <div style={{ padding: '22px 28px', borderBottom: '1px solid #2b2519' }}>
            <div className="sans" style={{ fontSize: 11, letterSpacing: 3, color: '#c9a227', marginBottom: 14 }}>OUTCOMES</div>
            {[['vindicated', '#7fb069'], ['condemned', '#c1443c'], ['rugged', '#8a7f63'], ['open', '#5a4f35']].map(([k, c]) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                <div className="sans" style={{ fontSize: 12, letterSpacing: 2, color: '#8a7f63', width: 110 }}>{k.toUpperCase()}</div>
                <div style={{ flex: 1, height: 10, background: '#1a1610', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: bar(st[k] || 0) + '%', height: '100%', background: c }} /></div>
                <div className="sans" style={{ fontSize: 12, color: '#e8e0cf', width: 70, textAlign: 'right' }}>
                  {st[k] || 0} · {bar(st[k] || 0)}%</div>
              </div>))}
          </div>
          <div className="sans" style={{ display: 'flex', flexWrap: 'wrap', borderBottom: '1px solid #2b2519' }}>
            <Num v={s.median_peak_x ? s.median_peak_x.toFixed(1) + '×' : '—'} label="MEDIAN PEAK" color="#c9a227" />
            <Num v={s.week.calls} label="CALLS THIS WEEK" />
            <Num v={s.week.callers} label="NEW CALLERS" />
            <Num v={s.week.snapshots_24h} label="SNAPS 24H" />
          </div>
          <div style={{ padding: '22px 28px', borderBottom: '1px solid #2b2519' }}>
            <div className="sans" style={{ fontSize: 11, letterSpacing: 3, color: '#c9a227', marginBottom: 14 }}>CHAINS</div>
            {Object.entries(s.chains || {}).map(([ch, n]) => (
              <div key={ch} className="sans" style={{ display: 'flex', gap: 12, fontSize: 13, color: '#8a7f63', marginBottom: 8 }}>
                <span style={{ color: '#e8e0cf', width: 100 }}>{ch}</span><span>{n} call{n === 1 ? '' : 's'}</span>
              </div>))}
          </div>
        </>)}
      </div>
      <aside className="siderail">
        {s && s.best && (
          <RailBox icon={TrendingUp} title="BEST CALL EVER">
            <RailRow href={'/coin/' + s.best.mint} left={'$' + s.best.coin + ' ↗'} right={s.best.peak_x.toFixed(1) + '×'} rightColor="#7fb069" />
            <RailRow href={'/profile/' + s.best.caller} left={'@' + s.best.caller} right="" />
          </RailBox>)}
        <RailBox icon={Scale} title="HOW SCORING WORKS">
          <p style={{ fontSize: 14, fontStyle: 'italic', color: '#9a8c6c', lineHeight: 1.7 }}>
            Median peak, never best peak. One lucky runner can't carry fifty rugs.</p>
        </RailBox>
        <SignInBox />
      </aside>
    </>
  );
}
