'use client';
// Shared receipt anatomy: avatar, seal, price line, engagement row.
import {
  Heart, Repeat, Quote, Eye, Flame, Hourglass,
  ShieldCheck, ShieldX, Skull, BadgeCheck, LogIn,
  Trophy, TrendingUp, Scale, Medal, Link2, Share2,
} from 'lucide-react';
import { avatar, fmtCount, timeAgo, fmtPrice, API_BASE } from '../lib/api';
import { useEffect, useState } from 'react';

const X_PATH = 'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z';
const GH_PATH = 'M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12';

export function XIcon({ size }) {
  return (<svg width={size || 17} height={size || 17} viewBox="0 0 24 24"
    fill="currentColor" aria-label="X"><path d={X_PATH} /></svg>);
}

export function GithubIcon({ size }) {
  return (<svg width={size || 17} height={size || 17} viewBox="0 0 24 24"
    fill="currentColor" aria-label="GitHub"><path d={GH_PATH} /></svg>);
}

export function Avatar({ url, name, size }) {
  const s = size || 44;
  const u = avatar(url);
  return (
    <div style={{ width: s, height: s, borderRadius: '50%', background: '#1a1610',
      border: '1px solid #2b2519', color: '#c9a227', fontFamily: 'Verdana,sans-serif',
      fontSize: s * 0.34, fontWeight: 700, display: 'flex', alignItems: 'center',
      justifyContent: 'center', flexShrink: 0, overflow: 'hidden' }}>
      {u ? <img src={u} alt={name || ''} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        : (name || '?').slice(0, 1).toUpperCase()}
    </div>
  );
}

export function PersonLine({ p, action, ts }) {
  return (
    <div className="sans" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 7 }}>
      <b style={{ color: '#f2ead6', fontWeight: 400 }}>{p.name || '@' + p.handle}</b>
      {p.verified && <BadgeCheck size={13} color="#7fb069" />}
      <span style={{ color: '#5a4f35' }}>@{p.handle} · {action}{ts ? ' · ' + timeAgo(ts) : ''}</span>
    </div>
  );
}

export function Seal({ seal, mult }) {
  const cls = seal === 'VINDICATED' ? { c: '#7fb069', I: ShieldCheck }
    : seal === 'CONDEMNED' ? { c: '#c1443c', I: ShieldX }
    : seal === 'RUGGED' ? { c: '#c1443c', I: Skull, fill: true }
    : { c: '#8a7f63', I: Hourglass };
  const label = seal + (mult !== null && mult !== undefined && seal !== 'UNDECIDED'
    ? ' · ' + mult.toFixed(1) + '×' : '');
  return (
    <span className="sans" style={{ fontSize: 11, letterSpacing: 2, padding: '6px 12px',
      borderRadius: 2, border: '1px solid ' + cls.c, color: cls.fill ? '#0c0a08' : cls.c,
      background: cls.fill ? cls.c : 'transparent',
      display: 'inline-flex', alignItems: 'center', gap: 7, whiteSpace: 'nowrap' }}>
      <cls.I size={12} />{label}
    </span>
  );
}

function actionText(r) {
  if (r.filed_via === 'form') return 'filed via form';
  if (r.filed_via === 'tag') return 'filed';
  return 'called';
}

export function Receipt({ r }) {
  const filer = r.filer || {};
  const nowTxt = r.now !== null && r.now !== undefined
    ? <b style={{ color: r.good ? '#7fb069' : '#c1443c', fontWeight: 400 }}>{fmtPrice(r.now)}</b>
    : <b style={{ fontWeight: 400 }}>awaiting snapshot</b>;
  return (
    <div className="rcard" style={{ borderBottom: '1px solid #2b2519', display: 'flex', gap: 14 }}>
      <Avatar url={filer.avatar} name={filer.name || filer.handle} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <PersonLine p={filer} action={actionText(r)} ts={r.ts} />
        <div style={{ fontSize: 17, margin: '8px 0', lineHeight: 1.55 }}>
          {r.coin && r.coin !== '?' && <span style={{ color: '#c9a227' }}>${r.coin} </span>}
          called by <a href={'/profile/' + r.caller.handle}
            style={{ color: '#f2ead6' }}>@{r.caller.handle}</a>
          {r.then ? ', entry ' + fmtPrice(r.then) : ''}
        </div>
        <a href={'/coin/' + r.mint} className="sans"
          style={{ fontSize: 12, color: '#8a7f63', background: '#121009',
            border: '1px solid #2b2519', borderRadius: 3, padding: '6px 10px',
            display: 'inline-block', margin: '2px 0 4px', letterSpacing: '.3px',
            textDecoration: 'none', wordBreak: 'break-all' }}>{r.mint}</a>
        <div className="sans" style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 12, flexWrap: 'wrap' }}>
          <Seal seal={r.seal} mult={r.mult} />
          {r.viral && <span className="sans" style={{ fontSize: 11, letterSpacing: 2, color: '#0c0a08',
            background: '#c9a227', padding: '6px 12px', borderRadius: 2,
            display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <Flame size={12} />VIRAL · {fmtCount(r.eng.views)} views</span>}
          <span style={{ fontSize: 13, color: '#8a7f63' }}>
            entry <b style={{ color: '#e8e0cf', fontWeight: 400 }}>{fmtPrice(r.then) || '—'}</b>
            {' · '}now {nowTxt}
            {r.peak_x ? <span>{' · '}peak <b style={{ color: '#c9a227', fontWeight: 400 }}>{r.peak_x.toFixed(1)}×</b></span> : ''}</span>
        </div>
        <div className="sans" style={{ display: 'flex', gap: 18, marginTop: 12, paddingTop: 12,
          borderTop: '1px solid #1a1610', fontSize: 12, color: '#5a4f35' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><Heart size={14} />{fmtCount(r.eng.likes)}</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><Repeat size={14} />{fmtCount(r.eng.reposts)}</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><Quote size={14} />{fmtCount(r.eng.quotes)}</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><Eye size={14} />{fmtCount(r.eng.views)}</span>
        </div>
      </div>
    </div>
  );
}

export function SignInBox() {
  // Signed in: mini profile (photo, name, followers). Otherwise: X login.
  const [prof, setProf] = useState(null);
  const [checked, setChecked] = useState(false);
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const m = await fetch(API_BASE + '/api/auth/me',
          { credentials: 'include', cache: 'no-store' }).then(r => r.json());
        if (!live || !m.handle) return;
        const p = await fetch(API_BASE + '/api/profile/' +
          encodeURIComponent(m.handle), { cache: 'no-store' }).then(r => r.json());
        if (live && p.profile) setProf(p.profile);
      } catch (e) { /* signed out */ }
      if (live) setChecked(true);
    })();
    return () => { live = false; };
  }, []);
  const btn = {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9,
    width: '100%', marginTop: 14, background: '#e8e0cf', color: '#0c0a08',
    fontWeight: 700, fontSize: 13, letterSpacing: 1, padding: 12,
    borderRadius: 4, textDecoration: 'none',
  };
  if (prof) {
    const u = avatar(prof.avatar);
    return (
      <div style={{ background: '#1a1610', border: '1px solid #c9a227', borderRadius: 6, padding: '18px 16px', marginBottom: 18 }}>
        <a href={'/profile/' + encodeURIComponent(prof.handle)}
          style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none' }}>
          <span className="tabava" style={{ width: 44, height: 44 }}>
            {u ? <img src={u} alt="" /> : <LogIn />}</span>
          <span>
            <span className="sans" style={{ display: 'block', fontSize: 14, fontWeight: 700, color: '#f2ead6' }}>
              @{prof.handle}</span>
            <span className="sans" style={{ display: 'block', fontSize: 11, letterSpacing: 1, color: '#8a7f63', marginTop: 4 }}>
              {fmtCount(prof.followers)} FOLLOWERS · {fmtCount(prof.following)} FOLLOWING</span>
          </span>
        </a>
      </div>
    );
  }
  return (
    <div style={{ background: '#1a1610', border: '1px solid #c9a227', borderRadius: 6, padding: '18px 16px', marginBottom: 18 }}>
      <p style={{ fontSize: 14, fontStyle: 'italic', color: '#9a8c6c', lineHeight: 1.6 }}>
        Sign in to claim your filings. Every call you file lands under your name.</p>
      {checked && (
        <a href={API_BASE + '/api/auth/login'} className="sans" style={btn}>
          <LogIn size={15} />SIGN IN WITH X</a>)}
    </div>
  );
}

export function RailBox({ icon: I, title, children }) {
  return (
    <div style={{ background: '#121009', border: '1px solid #2b2519', borderRadius: 6, padding: 16, marginBottom: 18 }}>
      <h3 className="sans" style={{ fontSize: 11, letterSpacing: 2, color: '#c9a227', marginBottom: 6,
        display: 'flex', alignItems: 'center', gap: 8 }}>
        <I size={14} />{title}</h3>
      {children}
    </div>
  );
}

export function RailRow({ left, right, rightColor }) {
  return (
    <div className="sans" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13,
      padding: '8px 0', borderTop: '1px solid #1a1610' }}>
      <span>{left}</span>
      <span style={{ color: rightColor || '#8a7f63' }}>{right}</span>
    </div>
  );
}

export { Trophy, TrendingUp, Scale, Medal, Link2, Share2, BadgeCheck };
