import { API_BASE, X_URL } from '../../lib/api';
import { XIcon } from '../../lib/components';

export default function SignIn({ searchParams }) {
  const failed = searchParams && searchParams.err;
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Sign in</h1>
          <div className="sub">One tap with X. No password, no new account.</div>
        </div>
        <div style={{ padding: 40, maxWidth: 560 }}>
          {failed && (
            <p style={{ fontSize: 15, color: '#c1443c', lineHeight: 1.7, marginBottom: 16 }}>
              That sign-in did not complete. Try once more.</p>
          )}
          <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7 }}>
            Signing in ties your filings to your name on your public record, and it
            unlocks the @urdheim tag: only signed-in handles get a reply.</p>
          <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7, marginTop: 14 }}>
            Filing through the form stays open either way. Sign-in is for credit.</p>
          <a href={API_BASE + '/api/auth/login'}
            className="sans"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9,
              marginTop: 26, background: '#e8e0cf', color: '#0c0a08', fontWeight: 700,
              fontSize: 13, letterSpacing: 1, padding: 14, borderRadius: 4,
              textDecoration: 'none' }}>
            <XIcon size={15} />SIGN IN</a>
          <p className="sans" style={{ fontSize: 11, letterSpacing: 1, color: '#5a4f35', marginTop: 16 }}>
            We read your handle, photo and bio. Nothing else. <a href={X_URL}>@Urdheim</a></p>
        </div>
      </div>
      <aside className="siderail" />
    </>
  );
}
