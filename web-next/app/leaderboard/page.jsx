'use client';
import { useState } from 'react';
import { callers, fmtAvg } from '../../lib/data';

export default function Leaderboard() {
  const [tab, setTab] = useState('all');
  const [open, setOpen] = useState('Cryptoceleb1');
  const shown = callers.filter((c) => tab === 'all' || c.kind === tab);
  return (
    <div className="wrap" style={{ paddingTop: 44 }}>
      <div className="eyebrow">THE ETERNAL RECORD</div>
      <h1 style={{ textAlign: 'center', fontSize: 56, letterSpacing: 10, margin: '12px 0 4px', fontWeight: 400 }}>URDHEIM</h1>
      <div style={{ textAlign: 'center', color: '#8a7f63', fontStyle: 'italic', marginBottom: 8 }}>every call remembered · every rug written in stone</div>
      <div style={{ textAlign: 'center', color: '#5a4f35', letterSpacing: 14, fontSize: 18, margin: '18px 0 34px' }}>ᚢᚱᚦ · ᚺᛖᛁ</div>
      <div style={{ height: 1, background: 'linear-gradient(90deg,transparent,#c9a227,transparent)', margin: '0 0 34px' }} />
      <div className="sans" style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 30 }}>
        {[['all', 'ALL CALLERS'], ['guilty', 'CONDEMNED'], ['clean', 'VINDICATED']].map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            style={{ background: tab === k ? '#c9a227' : 'transparent', border: '1px solid ' + (tab === k ? '#c9a227' : '#4a4132'),
              color: tab === k ? '#0c0a08' : '#b7a67f', padding: '9px 26px', fontSize: 13, letterSpacing: 2,
              cursor: 'pointer', borderRadius: 2, fontWeight: tab === k ? 700 : 400 }}>{label}</button>
        ))}
      </div>
      {shown.map((c) => (
        <div key={c.handle} onClick={() => setOpen(open === c.handle ? null : c.handle)}
          style={{ padding: '20px 22px', border: '1px solid ' + (open === c.handle ? '#c9a227' : '#2b2519'),
            borderRadius: 4, marginBottom: 12, background: '#121009', cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
            <div style={{ fontSize: 30, color: '#5a4f35', width: 52, fontStyle: 'italic' }}>{c.rank}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 21, color: '#f2ead6' }}><a href={'/caller/' + c.handle} onClick={(e) => e.stopPropagation()} style={{ color: 'inherit', textDecoration: 'none' }}>@{c.handle}</a></div>
              <div className="sans" style={{ fontSize: 13, color: '#8a7f63', marginTop: 3 }}>{c.calls} calls · {c.green} green · avg {fmtAvg(c.avg)}</div>
            </div>
            <div className="sans" style={{ display: 'flex', gap: 22, fontSize: 12, color: '#8a7f63' }}>
              <span><b className={c.green > c.red ? 'grn' : 'rd'} style={{ display: 'block', fontSize: 19, fontFamily: 'Georgia,serif' }}>{c.green}</b>green</span>
              <span><b className="rd" style={{ display: 'block', fontSize: 19, fontFamily: 'Georgia,serif' }}>{c.red}</b>red</span>
            </div>
            <div className={'seal ' + (c.seal === 'CONDEMNED' ? 'guilty' : c.seal === 'VINDICATED' ? 'clean' : 'mixed')}>{c.seal}</div>
          </div>
          {open === c.handle && (
            <div style={{ marginTop: 16, borderTop: '1px solid #2b2519', paddingTop: 16 }}>
              <div style={{ fontStyle: 'italic', fontSize: 15.5, lineHeight: 1.65, color: '#cfc3a4' }}>{c.verdict}</div>
              <div className="sans" style={{ marginTop: 12, fontSize: 12.5, color: '#9a8c6c', borderLeft: '2px solid ' + (c.worst.good ? '#7fb069' : '#c1443c'), padding: '8px 12px', background: '#00000044' }}>
                {c.worst.good ? 'best' : 'worst'} call: <b>{c.worst.coin}</b> {c.worst.then} → {c.worst.now} ({c.worst.ret}) · <a href={'/caller/' + c.handle} style={{ color: '#c9a227' }}>full file →</a>
              </div>
              <div className="sans" style={{ marginTop: 12, fontSize: 12.5 }}>
                {c.log.map(([t, r, good]) => (
                  <div key={t} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px dashed #2b2519', color: '#9a8c6c' }}>
                    <span>{t}</span><span className={good ? 'grn' : 'rd'} style={{ fontWeight: 700 }}>{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
      <div style={{ textAlign: 'center', color: '#5a4f35', fontSize: 13, fontStyle: 'italic', marginTop: 36 }}>
        tap a row to open its file · what is written here cannot be unwritten
      </div>
    </div>
  );
}
