'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ScrollText, Tag, SearchCheck, Stamp, Scale, ArrowRight, LogIn } from 'lucide-react';
import { apiStats } from '../lib/api';

const STEPS = [
  [Tag, 'Tag the call', 'Reply to any call post with @urdheim. That tag is your filing.'],
  [SearchCheck, 'The detective reads it', 'Every tagged post is judged: real call, soft shill, or just chatting. Only real calls enter the record.'],
  [Stamp, 'The price freezes', 'Entry price snapshots at the moment of the call, before the chart moves and the story changes.'],
  [Scale, 'The verdict lands', 'Open calls get repriced. Green holds, red condemns. The receipt updates itself.'],
];

export default function Landing() {
  const [stats, setStats] = useState(null);
  useEffect(() => { apiStats().then(setStats).catch(() => {}); }, []);
  return (
    <div className="land">
      <header className="landtop">
        <span className="landbrand">URDHEIM</span>
        <Link href="/feed" className="landin">OPEN THE RECORD</Link>
      </header>
      <main>
        <section className="hero">
          <p className="eyebrow">KOL accountability, on Solana and Robinhood Chain</p>
          <h1>Every call gets<br />a receipt.</h1>
          <p className="lede">
            Urdheim files memecoin calls made on X. Entry price frozen at the moment
            of the post, verdict when the chart speaks. No edits, no deletions,
            no "you had to be there".</p>
          <div className="ctas">
            <Link href="/feed" className="cta gold"><ScrollText size={15} />SEE LIVE RECEIPTS<ArrowRight size={15} /></Link>
            <Link href="/my" className="cta line"><LogIn size={15} />SIGN IN WITH X</Link>
          </div>
          {stats && (
            <div className="livebar">
              <span><b>{stats.calls}</b> receipts filed</span>
              <span><b>{stats.callers}</b> callers tracked</span>
            </div>)}
        </section>
        <section className="steps">
          {STEPS.map(([I, h, p], i) => (
            <div key={h} className="step">
              <div className="snum">0{i + 1}</div>
              <I size={20} color="#c9a227" />
              <h2>{h}</h2>
              <p>{p}</p>
            </div>))}
        </section>
        <section className="closer">
          <p>No account needed to file. Sign in only when you want the filings tied to your name, on your public record.</p>
          <Link href="/feed" className="cta gold"><ScrollText size={15} />OPEN THE RECORD<ArrowRight size={15} /></Link>
        </section>
      </main>
      <footer className="landfoot">
        <span>URDHEIM · SHILL RECEIPTS</span>
        <Link href="/how">How it works</Link>
      </footer>
    </div>
  );
}
