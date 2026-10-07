'use client';
import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ScrollText, Trophy, UserRound, Info } from 'lucide-react';

const NAV = [
  ['/', 'Live receipts', ScrollText],
  ['/leaderboard', 'Leaderboard', Trophy],
  ['/my', 'My receipts', UserRound],
  ['/how', 'How it works', Info],
];

export default function RootLayout({ children }) {
  const path = usePathname() || '/';
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="rail">
            <Link href="/" className="brand">URDHEIM<small>SHILL RECEIPTS</small></Link>
            <div style={{ height: 18 }} />
            {NAV.map(([href, label, I]) => (
              <Link key={href} href={href}
                className={'railnav' + (path === href ? ' on' : '')}>
                <I />{label}</Link>
            ))}
          </aside>
          {children}
        </div>
      </body>
    </html>
  );
}
