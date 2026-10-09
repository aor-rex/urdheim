'use client';
import { useEffect, useState } from 'react';
import { callOp } from './api';
import { ShieldCheck } from './components';

const sec = {
  border: '1px solid #c9a227', borderRadius: 6, background: '#121009',
  padding: '20px 22px', margin: '0 28px 18px',
};
const h = {
  fontSize: 11, letterSpacing: 3, color: '#c9a227', marginBottom: 12,
};
const btn = {
  background: 'none', border: '1px solid #2b2519', borderRadius: 4,
  color: '#e8e0cf', fontSize: 11, letterSpacing: 2, padding: '10px 14px',
  cursor: 'pointer',
};
const input = {
  background: '#0c0a08', border: '1px solid #2b2519', borderRadius: 4,
  color: '#e8e0cf', fontSize: 13, padding: '10px 12px', width: '100%',
  marginBottom: 10,
};
const row = { fontSize: 13, color: '#8a7f63', marginBottom: 8, lineHeight: 1.6 };

function Confirm({ expect, label, onFire }) {
  const [v, setV] = useState('');
  const ok = v.trim().toLowerCase() === expect.toLowerCase();
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <input value={v} onChange={(e) => setV(e.target.value)} placeholder={'type ' + expect}
        className="sans" style={{ ...input, marginBottom: 0, flex: 1 }} />
      <button disabled={!ok} onClick={() => { onFire(); setV(''); }} className="sans"
        style={{ ...btn, opacity: ok ? 1 : 0.35, borderColor: ok ? '#c1443c' : '#2b2519',
          color: ok ? '#c1443c' : '#e8e0cf' }}>{label}</button>
    </div>);
}

export default function OpsPanel() {
  const [queue, setQueue] = useState(null);
  const [errors, setErrors] = useState(null);
  const [log, setLog] = useState(null);
  const [msg, setMsg] = useState('');
  const [handle, setHandle] = useState('');
  const [callId, setCallId] = useState('');

  const refresh = () => {
    callOp('queue.view').then(setQueue).catch(() => {});
    callOp('errors.view').then(setErrors).catch(() => {});
    callOp('log.view').then(setLog).catch(() => {});
  };
  useEffect(refresh, []);

  const run = async (op, params, done) => {
    setMsg('');
    try {
      const r = await callOp(op, params);
      setMsg(op + ' ok' + (r.state ? ' → ' + r.state : ''));
      refresh();
      if (done) done();
    } catch (e) { setMsg(op + ' failed'); }
  };

  return (
    <div style={{ borderTop: '1px solid #2b2519', paddingTop: 22, marginTop: 6 }}>
      <div className="sans" style={{ display: 'flex', alignItems: 'center', gap: 8,
        fontSize: 13, letterSpacing: 4, color: '#c9a227', margin: '0 28px 16px' }}>
        <ShieldCheck size={15} />ADMIN</div>
      {msg && <div className="sans" style={{ ...row, margin: '0 28px 14px', color: '#c9a227' }}>{msg}</div>}

      <div className="sans" style={sec}>
        <div style={h}>INTAKE QUEUE</div>
        {!queue && <div style={row}>loading…</div>}
        {queue && Object.entries(queue.counts || {}).map(([k, n]) => (
          <div key={k} style={row}>{k}: <b style={{ color: '#e8e0cf' }}>{n}</b></div>))}
        {(queue && queue.queue || []).slice(0, 8).map((q, i) => {
          const u = String(q.caller || '—');
          const short = u.length > 24 ? u.slice(0, 16) + '…' + u.slice(-6) : u;
          return (
            <div key={i} style={{ ...row, fontSize: 13, color: '#e8e0cf' }}>
              <b style={{ color: q.status === 'rejected' ? '#c0574a' : '#7fb069' }}>{q.status}</b>
              {' · @' + short.replace(/^@/, '').split(':')[0]}
              <div style={{ fontSize: 11, color: '#8a7f63', wordBreak: 'break-all' }}>
                {(u.split(':')[1] || '') + ' · ' + String(q.at).slice(0, 16)}
              </div>
            </div>);
        })}
      </div>

      <div className="sans" style={sec}>
        <div style={h}>STUCK CALLS</div>
        {!errors && <div style={row}>loading…</div>}
        {errors && errors.stuck.length === 0 && <div style={row}>nothing stuck. the loop is healthy.</div>}
        {(errors && errors.stuck || []).map((c) => (
          <div key={c.id} style={{ ...row, display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ flex: 1 }}>#{c.id} ${c.coin} · @{c.caller}</span>
            <button onClick={() => run('snapshot.retry', { call_id: c.id })} className="sans" style={btn}>RETRY</button>
          </div>))}
      </div>

      <div className="sans" style={sec}>
        <div style={h}>ALLOWLIST</div>
        <input value={handle} onChange={(e) => setHandle(e.target.value)} placeholder="@handle" className="sans" style={input} />
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => run('allow.add', { handle }, () => setHandle(''))} className="sans" style={btn}>ADD</button>
          <button onClick={() => run('allow.remove', { handle }, () => setHandle(''))} className="sans" style={btn}>REMOVE</button>
        </div>
      </div>

      <div className="sans" style={sec}>
        <div style={h}>HIDE CALL</div>
        <div style={{ ...row, marginBottom: 10 }}>Vanishes from feed, board, coins, profiles. Typed confirm, logged.</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <input value={callId} onChange={(e) => setCallId(e.target.value)} placeholder="call id" className="sans" style={{ ...input, marginBottom: 0, flex: 1 }} />
        </div>
        {callId && <Confirm expect={'hide ' + callId} label="HIDE"
          onFire={() => run('call.hide', { call_id: Number(callId) }, () => setCallId(''))} />}
      </div>

      <div className="sans" style={sec}>
        <div style={h}>AUDIT LOG</div>
        {!log && <div style={row}>loading…</div>}
        {(log && log.log || []).slice(0, 15).map((l, i) => (
          <div key={i} style={{ ...row, wordBreak: 'break-all' }}>{String(l.at).slice(0, 16)} · @{l.by} · {l.op} {l.detail}</div>))}
        {(log && log.log || []).length === 0 && <div style={row}>no ops run yet.</div>}
      </div>
    </div>
  );
}
