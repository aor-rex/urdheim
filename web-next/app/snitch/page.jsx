'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';
const SITEKEY = process.env.NEXT_PUBLIC_TURNSTILE_SITEKEY || '1x00000000000000000000AA';

export default function Snitch() {
  const [done, setDone] = useState(false);
  const [err, setErr] = useState(null);
  if (typeof window !== 'undefined' && !document.querySelector('script[src*="turnstile"]')) {
    const s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
    s.async = true;
    document.head.appendChild(s);
  }
  async function submit(e) {
    e.preventDefault();
    setErr(null);
    const fd = new FormData(e.target);
    const token = document.querySelector('[name="cf-turnstile-response"]')?.value;
    try {
      const r = await fetch(API + '/api/snitch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_url: fd.get('post_url'),
          handle: fd.get('handle'),
          turnstile: token,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'rejected');
      setDone(d.duplicate ? 'already filed' : true);
    } catch (ex) {
      setErr(String(ex.message || ex));
    }
  }
  if (done) return (
    <div className="wrap" style={{ maxWidth: 640, paddingTop: 60, textAlign: 'center' }}>
      <div style={{ border: '1px solid #7fb069', borderRadius: 4, padding: 30, background: '#0e140d' }}>
        <h2 style={{ fontSize: 24, fontWeight: 400, color: '#7fb069' }}>{done === true ? 'Filed.' : 'Already filed.'}</h2>
        <p style={{ fontStyle: 'italic', color: '#9a8c6c', marginTop: 10, lineHeight: 1.7 }}>
          The detective will read the post, check for a real call, and snapshot the price if it qualifies.
          If this caller is new, two more snitches puts them on the watchlist.
        </p>
      </div>
    </div>
  );
  return (
    <div className="wrap" style={{ maxWidth: 640, paddingTop: 60, textAlign: 'center' }}>
      <div className="eyebrow">THE INFORMANT'S DOOR</div>
      <h1 style={{ fontSize: 48, fontWeight: 400, margin: '14px 0 8px' }}>Snitch a call</h1>
      <div style={{ fontStyle: 'italic', color: '#9a8c6c', lineHeight: 1.7 }}>Paste the post. We verify it, snapshot the price,<br />and the record grows. No account, no name taken.</div>
      <form style={{ marginTop: 36, textAlign: 'left' }} onSubmit={submit}>
        <label className="sans" style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#8a7f63', margin: '20px 0 8px' }}>POST LINK</label>
        <input required name="post_url" placeholder="https://x.com/someone/status/..."
          style={{ width: '100%', background: '#121009', border: '1px solid #2b2519', borderRadius: 4, color: '#f2ead6', padding: '14px 16px', fontSize: 15, fontFamily: 'Verdana,sans-serif', outline: 'none' }} />
        <label className="sans" style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#8a7f63', margin: '20px 0 8px' }}>CALLER'S HANDLE (IF KNOWN)</label>
        <input name="handle" placeholder="@someone"
          style={{ width: '100%', background: '#121009', border: '1px solid #2b2519', borderRadius: 4, color: '#f2ead6', padding: '14px 16px', fontSize: 15, fontFamily: 'Verdana,sans-serif', outline: 'none' }} />
        <div className="cf-turnstile" data-sitekey={SITEKEY} style={{ marginTop: 22 }}></div>
        {err && <div className="sans" style={{ color: '#c1443c', fontSize: 13, marginTop: 12 }}>{err}</div>}
        <button type="submit" className="sans" style={{ width: '100%', marginTop: 22, background: '#c9a227', color: '#0c0a08', fontWeight: 700, fontSize: 13, letterSpacing: 2, padding: 16, border: 'none', borderRadius: 3, cursor: 'pointer' }}>FILE IT IN THE RECORD</button>
      </form>
      <div style={{ marginTop: 30, textAlign: 'left', fontStyle: 'italic', color: '#8a7f63', fontSize: 14, lineHeight: 1.9 }}>
        The house rules, plainly:<br />
        <b className="gold">1.</b> It must be a real post with a real call — fakes go in the bin.<br />
        <b className="gold">2.</b> Your snitch only nominates for tracking — the detective writes the verdict, never votes.<br />
        <b className="gold">3.</b> Three separate snitches puts a caller on the watchlist.
      </div>
    </div>
  );
}
