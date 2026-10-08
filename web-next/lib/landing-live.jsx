'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';
import { apiFeed, apiStats, timeAgo } from './api';

// Live islands on the server-rendered landing: counts + fresh 3.
function useLive() {
  const [stats, setStats] = useState(null);
  const [fresh, setFresh] = useState([]);
  useEffect(() => {
    apiStats().then(setStats).catch(() => {});
    apiFeed(3).then((d) => setFresh(d.receipts || [])).catch(() => {});
  }, []);
  return { stats, fresh };
}

export function LiveBar() {
  const { stats } = useLive();
  if (!stats) return null;
  return (
    <div className="livebar">
      <span><b>{stats.calls}</b> receipts filed</span>
      <span><b>{stats.callers}</b> callers tracked</span>
    </div>);
}

export function FreshRows() {
  const { fresh } = useLive();
  if (fresh.length === 0) return null;
  return (
    <section className="fresh">
      <div className="freshhead">
        <span>FRESH FROM THE RECORD</span>
        <Link href="/feed">view all<ArrowUpRight size={13} /></Link>
      </div>
      {fresh.map((r, i) => (
        <Link key={r.mint + i} href="/feed" className="freshrow">
          <span className="ftick">{r.coin && r.coin !== '?' ? '$' + r.coin : '◇'}</span>
          <span className="fwhat">called by @{r.caller.handle}</span>
          <span className={'fseal ' + (r.seal === 'VINDICATED' ? 'g' : r.seal === 'CONDEMNED' ? 'r' : '')}>{r.seal}</span>
          <span className="fts">{timeAgo(r.ts)}</span>
        </Link>))}
    </section>);
}
