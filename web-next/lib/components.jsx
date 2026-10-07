'use client';
// Shared receipt anatomy: avatar, seal, price line, engagement row.
import {
  Heart, Repeat, Quote, Eye, Flame, Hourglass,
  ShieldCheck, ShieldX, BadgeCheck, LogIn,
  Trophy, TrendingUp, Scale, Medal, Link2, Share2,
} from 'lucide-react';
import { avatar, fmtCount, timeAgo, fmtPrice } from '../lib/api';

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
    : seal === 'CONDEMNED' ? { c: '#c1443c', I: ShieldX } : { c: '#8a7f63', I: Hourglass };
  const label = seal + (mult !== null && mult !== undefined && seal !== 'UNDECIDED'
    ? ' · ' + mult.toFixed(1) + '×' : '');
  return (
    <span className="sans" style={{ fontSize: 11, letterSpacing: 2, padding: '6px 12px',
      borderRadius: 2, border: '1px solid ' + cls.c, color: cls.c,
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
    <div style={{ borderBottom: '1px solid #2b2519', padding: '20px 28px', display: 'flex', gap: 14 }}>
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
            {' · '}now {nowTxt}</span>
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
  return (
    <div style={{ background: '#1a1610', border: '1px solid #c9a227', borderRadius: 6, padding: '18px 16px', marginBottom: 18 }}>
      <p style={{ fontSize: 14, fontStyle: 'italic', color: '#9a8c6c', lineHeight: 1.6 }}>
        Sign in to collect your own receipts. Every call you file lands on your public record.</p>
      <button className="sans" disabled title="X sign-in lands with OAuth creds"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9, width: '100%',
          marginTop: 14, background: '#e8e0cf', color: '#0c0a08', fontWeight: 700, fontSize: 13,
          letterSpacing: 1, padding: 12, border: 'none', borderRadius: 4, cursor: 'not-allowed', opacity: 0.55 }}>
        <LogIn size={15} />SIGN IN WITH X</button>
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
