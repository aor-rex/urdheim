'use client';
import { useEffect, useState } from 'react';
import { apiFeed, apiLeaderboard, fmtAvg, fmtCount } from '../../lib/api';
import { Receipt, SignInBox, RailBox, RailRow, Trophy, TrendingUp } from '../../lib/components';

export default function Feed() {
  const [receipts, setReceipts] = useState(null);
  const [board, setBoard] = useState([]);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiFeed().then((d) => setReceipts(d.receipts)).catch((e) => setErr(String(e)));
    apiLeaderboard().then((d) => setBoard((d.callers || []).slice(0, 3))).catch(() => {});
  }, []);
  const heating = (receipts || []).filter((r) => r.viral).slice(0, 5);
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Live receipts</h1>
          <div className="sub">Tag @urdheim on a call post. The detective reads it, snapshots the price, writes the receipt here.</div>
        </div>
        {err && <div style={{ padding: 40, color: '#c1443c' }} className="sans">api down: {err} — is ./run.sh api running?</div>}
        {!err && !receipts && <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>reading the record…</div>}
        {receipts && receipts.length === 0 && (
          <div style={{ padding: 40, fontStyle: 'italic', color: '#8a7f63' }}>
            No receipts yet. The next tagged call lands here.</div>)}
        {(receipts || []).map((r, i) => <Receipt key={r.mint + i} r={r} />)}
      </div>
      <aside className="siderail">
        <RailBox icon={Trophy} title="TOP CALLERS">
          {board.length === 0 && <RailRow left="reading the record" right="…" />}
          {board.map((c, i) => (
            <RailRow key={c.handle} left={(i + 1) + ' · @' + c.handle}
              right={c.calls ? fmtAvg(c.avg) + ' avg' : 'pending'} />))}
        </RailBox>
        <RailBox icon={TrendingUp} title="HEATING UP">
          {heating.length === 0 && <RailRow left="nothing viral" right="yet" />}
          {heating.map((r) => (
            <RailRow key={r.mint} left={'$' + r.coin} right={fmtCount(r.eng.views) + ' views'} />))}
        </RailBox>
        <SignInBox />
      </aside>
    </>
  );
}
