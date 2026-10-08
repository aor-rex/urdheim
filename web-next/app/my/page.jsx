'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { fetchMe } from '../../lib/api';

// /my has no page. Signed in: your public profile. Otherwise: sign in.
export default function My() {
  const router = useRouter();
  useEffect(() => {
    fetchMe()
      .then(m => router.replace(m.handle
        ? '/profile/' + encodeURIComponent(m.handle) : '/signin'))
      .catch(() => router.replace('/signin'));
  }, [router]);
  return (
    <div className="feedcol">
      <div style={{ padding: 40 }}>
        <p style={{ fontSize: 16, color: '#5a4f35' }}>Checking…</p>
      </div>
    </div>
  );
}
