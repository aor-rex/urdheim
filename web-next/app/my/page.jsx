'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { SignInBox } from '../../lib/components';
import { API_BASE } from '../../lib/api';

export default function My() {
  const [handle, setHandle] = useState(null);
  const [done, setDone] = useState(false);
  useEffect(() => {
    fetch(API_BASE + '/api/auth/me', { credentials: 'include', cache: 'no-store' })
      .then(r => r.json()).then(m => setHandle(m.handle || null))
      .catch(() => {}).finally(() => setDone(true));
  }, []);
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>My receipts</h1>
          <div className="sub">Your filings, under your name.</div>
        </div>
        <div style={{ padding: 40, maxWidth: 560 }}>
          {!done && <p style={{ fontSize: 16, color: '#5a4f35' }}>Checking…</p>}
          {done && handle && (
            <>
              <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7 }}>
                Signed in as <span className="gold">@{handle}</span>.</p>
              <p style={{ marginTop: 14 }}>
                <Link href={'/profile/' + encodeURIComponent(handle)}>
                  View my public profile</Link></p>
            </>
          )}
          {done && !handle && (
            <>
              <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7 }}>
                Nobody is signed in on this browser. Sign in and your filings
                land under your name.</p>
              <p style={{ marginTop: 14 }}>
                <Link href="/signin">Sign in with X</Link></p>
            </>
          )}
        </div>
      </div>
      <aside className="siderail"><SignInBox /></aside>
    </>
  );
}
