import { API_BASE, X_URL } from '../../lib/api';
import { XIcon } from '../../lib/components';

export default function SignIn({ searchParams }) {
  const failed = searchParams && searchParams.err;
  return (
    <div style={{
      gridColumn: '1 / -1', display: 'flex', alignItems: 'center',
      justifyContent: 'center', minHeight: 'calc(100vh - 220px)', padding: 24,
    }}>
      <div style={{ width: '100%', maxWidth: 560, textAlign: 'center' }}>
        <div style={{ fontSize: 15, letterSpacing: 6, color: '#5a4f35' }}
          className="sans">URDHEIM</div>
        <h1 style={{ fontSize: 54, fontWeight: 400, margin: '18px 0 0' }}>
          Sign in</h1>
        <div className="sans" style={{ fontSize: 12, letterSpacing: 2, color: '#5a4f35', marginTop: 12 }}>
          ONE TAP WITH X. NO PASSWORD, NO NEW ACCOUNT.</div>
        <div style={{ marginTop: 30, padding: 34, background: '#1a1610',
          border: '1px solid #c9a227', borderRadius: 8 }}>
          {failed && (
            <p style={{ fontSize: 15, color: '#c1443c', lineHeight: 1.7, marginBottom: 16 }}>
              That sign-in did not complete. Try once more.</p>
          )}
          <p style={{ fontSize: 17, color: '#9a8c6c', lineHeight: 1.7 }}>
            Signing in ties your filings to your name on your public record, and it
            unlocks the @urdheim tag: only signed-in handles get a reply.</p>
          <p style={{ fontSize: 17, color: '#9a8c6c', lineHeight: 1.7, marginTop: 14 }}>
            Filing through the form stays open either way. Sign-in is for credit.</p>
          <a href={API_BASE + '/api/auth/login'}
            className="sans"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              marginTop: 28, background: '#e8e0cf', color: '#0c0a08', fontWeight: 700,
              fontSize: 15, letterSpacing: 1, padding: 17, borderRadius: 4,
              textDecoration: 'none' }}>
            <XIcon size={17} />SIGN IN</a>
          <p className="sans" style={{ fontSize: 12, letterSpacing: 1, color: '#5a4f35', marginTop: 18 }}>
            We read your handle, photo and bio. Nothing else. <a href={X_URL}>@Urdheim</a></p>
        </div>
      </div>
    </div>
  );
}
