'use client';
import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ScrollText, Trophy, UserRound, Info } from 'lucide-react';
import { API_BASE, avatar } from '../lib/api';
import { XIcon, GithubIcon } from '../lib/components';

const NAV = [
  ['/feed', 'Live receipts', 'Feed', ScrollText],
  ['/leaderboard', 'Leaderboard', 'Board', Trophy],
  ['/my', 'My receipts', 'Mine', UserRound],
  ['/how', 'Help', 'Help', Info],
];

function Avatar() {
  // Signed-in photo from the profiles cache. Placeholder ring until then.
  const [img, setImg] = useState('');
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const me = await fetch(API_BASE + '/api/auth/me',
          { credentials: 'include', cache: 'no-store' }).then(r => r.json());
        if (!live || !me.handle) return;
        const p = await fetch(API_BASE + '/api/profile/' +
          encodeURIComponent(me.handle), { cache: 'no-store' }).then(r => r.json());
        if (live && p.profile && p.profile.avatar) setImg(avatar(p.profile.avatar));
      } catch (e) { /* signed out: keep the ring */ }
    })();
    return () => { live = false; };
  }, []);
  return (<span className="tabava">{img ? <img src={img} alt="" /> : <UserRound />}</span>);
}

export default function RootLayout({ children }) {
  const path = usePathname() || '/';
  const cur = path.replace(/\/+$/, '') || '/';
  if (path === '/') return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="rail">
            <Link href="/" className="brand">URDHEIM<small>SHILL RECEIPTS</small></Link>
            <div style={{ height: 18 }} />
            {NAV.map(([href, label, , I]) => (
              <Link key={href} href={href}
                className={'railnav' + (cur === href ? ' on' : '')}>
                <I />{label}</Link>
            ))}
          </aside>
          <div className="mobilebar">
            <Link href="/" className="brand">URDHEIM</Link>
            <Link href="/signin" className="in">SIGN IN</Link>
          </div>
          {children}
          <nav className="mobiletabs">
            {NAV.map(([href, , short, I]) => (
              <Link key={href} href={href} className={cur === href ? 'on' : ''}>
                {href === '/my' ? <Avatar /> : <I />}{short}</Link>
            ))}
          </nav>
        </div>
        <footer className="appfoot">
          <span>URDHEIM — SHILL RECEIPTS</span>
          <span className="social">
            <a href="https://x.com/Urdheim" target="_blank" rel="noreferrer"><XIcon /></a>
            <a href="https://github.com/aor-rex/urdheim" target="_blank" rel="noreferrer"><GithubIcon /></a>
          </span>
        </footer>
      </body>
    </html>
  );
}
