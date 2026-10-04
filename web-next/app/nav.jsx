'use client';
import { usePathname } from 'next/navigation';
import { X_URL } from '../lib/data';

export default function Nav() {
  const p = usePathname();
  const cls = (href) => (p === href ? 'on' : '');
  return (
    <div className="nav">
      <a className="logo" href="/">URDHEIM</a>
      <a className={cls('/leaderboard')} href="/leaderboard">LEADERBOARD</a>
      <a className={cls('/snitch')} href="/snitch">SNITCH</a>
      <a className="x" href={X_URL}>FOLLOW HEIMDALL</a>
    </div>
  );
}
