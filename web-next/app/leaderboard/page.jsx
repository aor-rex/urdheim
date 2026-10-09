'use client';
import { useEffect, useState } from 'react';
import { apiFeed, apiLeaderboard, fmtAvg, fmtCount, warmProfile } from '../../lib/api';
import { Avatar, RailBox, RailRow, SignInBox, Scale, TrendingUp } from '../../lib/components';

export default function Leaderboard() {
  const [callers, setCallers] = useState(null);
  const [hot, setHot] = useState([]);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiLeaderboard().then((d) => setCallers(d.callers)).catch((e) => setErr(String(e)));
    apiFeed().then((d) => setHot((d.receipts || []).filter((r) => r.viral).slice(0, 5))).catch(() => {});
  }, []);
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Leaderboard</h1>
          <div className="sub">Ranked by average return on closed calls. Open calls sit out until the snapshotter reprices them.</div>
        </div>
        {err && <div style={{ padding: 40, color: '#c1443c' }} className="sans">api down: {err} — is ./run.sh api running?</div>}
        {!err && !callers && <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>reading the record…</div>}
        {(callers || []).map((c, i) => {
          const p = c.profile || {};
          const scored = (c.green || 0) + (c.red || 0);
          return (
            <div key={c.handle} style={{ display: 'flex', alignItems: 'center', gap: 16,
              borderBottom: '1px solid #2b2519', padding: '18px 28px' }}>
              <div className="sans" style={{ fontSize: 13, color: '#5a4f35', width: 26 }}>{i + 1}</div>
              <Avatar url={p.avatar} name={p.name || c.handle} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 17 }}>
                  <a href={'/profile/' + c.handle} onMouseEnter={() => warmProfile(c.handle)} style={{ color: '#f2ead6', textDecoration: 'none' }}>
                    {p.name && p.name !== c.handle ? p.name + ' ' : ''}<span style={{ color: '#8a7f63' }}>@{c.handle}</span></a>
                </div>
                <div className="sans" style={{ fontSize: 12, color: '#8a7f63', marginTop: 5 }}>
                  {c.calls} call{c.calls === 1 ? '' : 's'} · {c.green} green · {scored} scored</div>
              </div>
              <div className="sans" style={{ fontSize: 20, width: 110, textAlign: 'right',
                color: scored ? (c.avg >= 0 ? '#7fb069' : '#c1443c') : '#8a7f63' }}>
                {scored ? fmtAvg(c.avg) : '—'}</div>
            </div>
          );
        })}
      </div>
      <aside className="siderail">
        <RailBox icon={Scale} title="HOW RANKING WORKS">
          <p style={{ fontSize: 14, fontStyle: 'italic', color: '#9a8c6c', lineHeight: 1.7 }}>
            Closed calls only. A call closes when the snapshotter reprices it.</p>
        </RailBox>
        <RailBox icon={TrendingUp} title="HEATING UP">
          {hot.length === 0 && <RailRow left="nothing viral" right="yet" />}
          {hot.map((r) => (
            <RailRow key={r.mint} left={'$' + r.coin} right={fmtCount(r.eng.views) + ' views'} />))}
        </RailBox>
        <SignInBox />
      </aside>
    </>
  );
}
