'use client';
import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ScrollText, Trophy, UserRound, Info } from 'lucide-react';

const NAV = [
  ['/feed', 'Live receipts', 'Feed', ScrollText],
  ['/leaderboard', 'Leaderboard', 'Board', Trophy],
  ['/my', 'My receipts', 'Mine', UserRound],
  ['/how', 'How it works', 'How', Info],
];

export default function RootLayout({ children }) {
  const path = usePathname() || '/';
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
                className={'railnav' + (path === href ? ' on' : '')}>
                <I />{label}</Link>
            ))}
          </aside>
          <div className="mobilebar">
            <Link href="/" className="brand">URDHEIM</Link>
            <Link href="/my" className="in">SIGN IN</Link>
          </div>
          {children}
          <nav className="mobiletabs">
            {NAV.map(([href, , short, I]) => (
              <Link key={href} href={href} className={path === href ? 'on' : ''}>
                <I />{short}</Link>
            ))}
          </nav>
        </div>
      </body>
    </html>
  );
}
