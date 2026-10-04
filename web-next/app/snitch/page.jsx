'use client';
import { useState } from 'react';

export default function Snitch() {
  const [done, setDone] = useState(false);
  if (done) return (
    <div className="wrap" style={{ maxWidth: 640, paddingTop: 60, textAlign: 'center' }}>
      <div style={{ border: '1px solid #7fb069', borderRadius: 4, padding: 30, background: '#0e140d' }}>
        <h2 style={{ fontSize: 24, fontWeight: 400, color: '#7fb069' }}>Filed.</h2>
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
      <form style={{ marginTop: 36, textAlign: 'left' }} onSubmit={(e) => { e.preventDefault(); setDone(true); }}>
        <label className="sans" style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#8a7f63', margin: '20px 0 8px' }}>POST LINK</label>
        <input required placeholder="https://x.com/someone/status/..."
          style={{ width: '100%', background: '#121009', border: '1px solid #2b2519', borderRadius: 4, color: '#f2ead6', padding: '14px 16px', fontSize: 15, fontFamily: 'Verdana,sans-serif', outline: 'none' }} />
        <label className="sans" style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#8a7f63', margin: '20px 0 8px' }}>CALLER'S HANDLE (IF KNOWN)</label>
        <input placeholder="@someone"
          style={{ width: '100%', background: '#121009', border: '1px solid #2b2519', borderRadius: 4, color: '#f2ead6', padding: '14px 16px', fontSize: 15, fontFamily: 'Verdana,sans-serif', outline: 'none' }} />
        <div className="sans" style={{ border: '1px dashed #4a4132', borderRadius: 4, padding: 22, marginTop: 22, fontSize: 13, color: '#8a7f63' }}>[ cloudflare turnstile widget goes here ]</div>
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
