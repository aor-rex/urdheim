import Link from 'next/link';
import { ScrollText, Tag, SearchCheck, Stamp, Scale, ArrowRight } from 'lucide-react';
import { XIcon, GithubIcon } from '../lib/components';
import { ScrambleWord } from '../lib/hero';
import { LiveBar, FreshRows } from '../lib/landing-live';

const SITE = process.env.NEXT_PUBLIC_SITE || 'https://urdheim.zone.id';

export const metadata = {
  metadataBase: new URL(SITE),
  title: 'Urdheim — every call gets a receipt',
  description: 'KOL accountability for memecoins on Solana and Robinhood Chain. Calls filed from X, entry frozen, verdict when the chart speaks.',
  openGraph: {
    title: 'Urdheim — every call gets a receipt',
    description: 'Memecoin calls filed from X. Entry frozen at the post, verdict when the chart speaks.',
    url: SITE,
    siteName: 'Urdheim',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Urdheim — every call gets a receipt',
    description: 'Memecoin calls filed from X. Entry frozen at the post, verdict when the chart speaks.',
  },
};

const STEPS = [
  [Tag, 'Tag the call', 'Reply to any call post with @urdheim. That tag is your filing.'],
  [SearchCheck, 'The detective reads it', 'Every tagged post is judged: real call, soft shill, or just chatting. Only real calls enter the record.'],
  [Stamp, 'The price freezes', 'Entry price snapshots at the moment of the call, before the chart moves and the story changes.'],
  [Scale, 'The verdict lands', 'Open calls get repriced. Green holds, red condemns. The receipt updates itself.'],
];

export default function Landing() {
  return (
    <div className="land">
      <header className="landtop">
        <span className="landbrand">
          <img src="/logo.svg" alt="Urdheim" width={30} height={30} />URDHEIM</span>
        <Link href="/feed" className="landin">OPEN THE RECORD</Link>
      </header>
      <main>
        <section className="hero">
          <p className="eyebrow">KOL accountability, on Solana and Robinhood Chain</p>
          <h1>Every call gets<br />a <ScrambleWord /></h1>
          <p className="lede">
            Urdheim files memecoin calls made on X. Entry price frozen at the moment
            of the post, verdict when the chart speaks. No edits, no deletions,
            no "you had to be there".</p>
          <div className="ctas">
            <Link href="/feed" className="cta gold"><ScrollText size={15} />SEE LIVE RECEIPTS<ArrowRight size={15} /></Link>
            <Link href="/my" className="cta line"><XIcon size={15} />SIGN IN</Link>
          </div>
          <LiveBar />
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
        <FreshRows />
      </main>
      <footer className="landfoot">
        <span className="footbrand">
          <img src="/logo.svg" alt="Urdheim" width={20} height={20} />URDHEIM · SHILL RECEIPTS</span>
        <div className="footlinks">
          <Link href="/how">Help</Link>
          <a href="https://x.com/Urdheim" target="_blank" rel="noreferrer" aria-label="X"><XIcon size={16} /></a>
          <a href="https://github.com/aor-rex/urdheim" target="_blank" rel="noreferrer" aria-label="GitHub"><GithubIcon size={16} /></a>
        </div>
      </footer>
    </div>
  );
}
