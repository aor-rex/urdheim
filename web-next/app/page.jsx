'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ScrollText, Tag, SearchCheck, Stamp, Scale, ArrowRight, ArrowUpRight } from 'lucide-react';
import { apiFeed, apiStats, timeAgo } from '../lib/api';
import { XIcon, GithubIcon } from '../lib/components';

const STEPS = [
  [Tag, 'Tag the call', 'Reply to any call post with @urdheim. That tag is your filing.'],
  [SearchCheck, 'The detective reads it', 'Every tagged post is judged: real call, soft shill, or just chatting. Only real calls enter the record.'],
  [Stamp, 'The price freezes', 'Entry price snapshots at the moment of the call, before the chart moves and the story changes.'],
  [Scale, 'The verdict lands', 'Open calls get repriced. Green holds, red condemns. The receipt updates itself.'],
];

const WORDS = [
  { t: 'απόδειξη', c: 'greek' },
  { t: 'receipt', c: 'latin' },
];

function ReceiptWord() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setI(v => (v + 1) % WORDS.length), 5200);
    return () => clearInterval(id);
  }, []);
  const w = WORDS[i];
  return (
    <span key={i} className={'swapword ' + w.c} aria-label={w.t}>
      {w.t.split('').map((ch, k) => (
        <span key={k} className="swapch" style={{ animationDelay: (k * 0.3) + 's' }}>
          {ch === ' ' ? ' ' : ch}</span>
      ))}
    </span>
  );
}

export default function Landing() {
  const [stats, setStats] = useState(null);
  const [fresh, setFresh] = useState([]);
  useEffect(() => {
    apiStats().then(setStats).catch(() => {});
    apiFeed(3).then((d) => setFresh(d.receipts || [])).catch(() => {});
  }, []);
  return (
    <div className="land">
      <header className="landtop">
        <span className="landbrand">URDHEIM</span>
        <Link href="/feed" className="landin">OPEN THE RECORD</Link>
      </header>
      <main>
        <section className="hero">
          <p className="eyebrow">KOL accountability, on Solana and Robinhood Chain</p>
          <h1>Every call gets<br />a <ReceiptWord /></h1>
          <p className="lede">
            Urdheim files memecoin calls made on X. Entry price frozen at the moment
            of the post, verdict when the chart speaks. No edits, no deletions,
            no "you had to be there".</p>
          <div className="ctas">
            <Link href="/feed" className="cta gold"><ScrollText size={15} />SEE LIVE RECEIPTS<ArrowRight size={15} /></Link>
            <Link href="/my" className="cta line"><XIcon size={15} />SIGN IN WITH X</Link>
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
        {fresh.length > 0 && (
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
          </section>)}
      </main>
      <footer className="landfoot">
        <span>URDHEIM · SHILL RECEIPTS</span>
        <div className="footlinks">
          <Link href="/how">Help</Link>
          <a href="https://x.com/Urdheim" target="_blank" rel="noreferrer" aria-label="X"><XIcon size={16} /></a>
          <a href="https://github.com/aor-rex/urdheim" target="_blank" rel="noreferrer" aria-label="GitHub"><GithubIcon size={16} /></a>
        </div>
      </footer>
    </div>
  );
}
