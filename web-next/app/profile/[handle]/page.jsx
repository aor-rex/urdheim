'use client';
import { use, useEffect, useState } from 'react';
import { apiProfile, fmtAvg, fmtCount, fetchMe, signOut } from '../../../lib/api';
import { Avatar, Receipt, RailBox, RailRow, SignInBox, Medal, Link2, Share2, BadgeCheck } from '../../../lib/components';
import { LogOut } from 'lucide-react';

export default function Profile({ params }) {
  const { handle } = use(params);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [mine, setMine] = useState(false);
  const [signedOut, setSignedOut] = useState(false);
  useEffect(() => {
    apiProfile(handle).then(setData).catch((e) => setErr(String(e)));
    fetchMe().then(m => {
      if (m.handle && m.handle.toLowerCase() === String(handle).toLowerCase()) setMine(true);
      if (!m.handle) setSignedOut(true);
    }).catch(() => setSignedOut(true));
  }, [handle]);
  if (err) return (
    <><div className="feedcol"><div style={{ padding: 40 }} className="sans">no record on @{handle} yet.</div></div>
      <aside className="siderail"><SignInBox /></aside></>);
  if (!data) return (
    <><div className="feedcol"><div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>pulling the file…</div></div>
      <aside className="siderail"><SignInBox /></aside></>);
  const { profile: p, stats: s, receipts } = data;
  const best = receipts.filter((r) => r.mult !== null)
    .sort((a, b) => b.mult - a.mult)[0];
  const chains = {};
  receipts.forEach((r) => { chains[r.chain] = (chains[r.chain] || 0) + 1; });
  return (
    <>
      <div className="feedcol">
        <div style={{ padding: 28, borderBottom: '1px solid #2b2519', display: 'flex', gap: 18, alignItems: 'center' }}>
          <Avatar url={p.avatar} name={p.name} size={72} />
          <div>
            <h1 style={{ fontSize: 30, fontWeight: 400, display: 'flex', alignItems: 'center', gap: 8 }}>
              {p.name}{p.verified && <BadgeCheck size={20} color="#7fb069" />}</h1>
            <div className="sans" style={{ fontSize: 12, color: '#5a4f35', marginTop: 6, letterSpacing: 1 }}>
              @{p.handle}</div>
            {p.bio && <div style={{ fontSize: 15, fontStyle: 'italic', color: '#9a8c6c', marginTop: 8 }}>{p.bio}</div>}
            <div className="sans" style={{ display: 'flex', gap: 18, fontSize: 13, color: '#8a7f63', marginTop: 10 }}>
              <span><b style={{ color: '#e8e0cf', fontWeight: 400 }}>{fmtCount(p.followers)}</b> followers</span>
              <span><b style={{ color: '#e8e0cf', fontWeight: 400 }}>{fmtCount(p.following)}</b> following</span>
            </div>
            {mine && (
              <button
                onClick={async () => { await signOut(); window.location.href = '/feed'; }}
                className="sans"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: 14, background: 'none', border: '1px solid #2b2519', borderRadius: 4, color: '#5a4f35', fontSize: 11, letterSpacing: 2, padding: '9px 14px', cursor: 'pointer' }}>
                <LogOut size={13} />SIGN OUT</button>)}
          </div>
        </div>
        <div className="sans" style={{ display: 'flex', borderBottom: '1px solid #2b2519' }}>
          {[[s.filed, 'FILED'], [s.verified, 'SCORED'],
            [s.scored ? fmtAvg(s.avg) : '—', 'AVG RETURN'],
          ].map(([n, l]) => (
            <div key={l} style={{ flex: 1, textAlign: 'center', padding: '16px 0', borderRight: '1px solid #2b2519' }}>
              <div style={{ fontSize: 22 }}>{n}</div>
              <div style={{ fontSize: 11, letterSpacing: 2, color: '#5a4f35', marginTop: 5 }}>{l}</div>
            </div>))}
        </div>
        {signedOut && (<div style={{ padding: '18px 28px 0' }}><SignInBox /></div>)}
        {receipts.map((r, i) => <Receipt key={r.mint + i} r={r} />)}
        {receipts.length === 0 && (
          <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>
            Nothing filed yet. Tag @urdheim on a call post and it lands here.</div>)}
      </div>
      <aside className="siderail">
        {best && (
          <RailBox icon={Medal} title="BEST CALL">
            <RailRow href={'/coin/' + best.mint} left={'$' + best.coin + ' ↗'} right={best.mult.toFixed(1) + '×'} rightColor="#7fb069" />
            <RailRow left="filed" right={best.ts ? best.ts.slice(0, 10) : ''} />
          </RailBox>)}
        {Object.keys(chains).length > 0 && (
          <RailBox icon={Link2} title="CHAINS FILED ON">
            {Object.entries(chains).map(([ch, n]) => (
              <RailRow key={ch} left={ch} right={n} />))}
          </RailBox>)}
        <button className="sans" onClick={() => navigator.clipboard && navigator.clipboard.writeText(window.location.href)}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9, width: '100%',
            background: 'transparent', border: '1px solid #c9a227', color: '#c9a227', fontSize: 12,
            letterSpacing: 2, padding: 12, borderRadius: 4, cursor: 'pointer' }}>
          <Share2 size={14} />SHARE RECORD</button>
      </aside>
    </>
  );
}
