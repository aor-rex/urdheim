import { SignInBox } from '../../lib/components';

export default function My() {
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>My receipts</h1>
          <div className="sub">Your filings, your record. Sign in to claim it.</div>
        </div>
        <div style={{ padding: 40, maxWidth: 560 }}>
          <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7 }}>
            Nobody is signed in on this browser. Once X sign-in is live, this page shows
            every call you filed, your hit rate, and your rank among filers.</p>
          <p style={{ fontSize: 16, color: '#9a8c6c', lineHeight: 1.7, marginTop: 14 }}>
            Until then, your filings still count. They sit on the receipts of the calls
            you tagged, waiting for your name.</p>
        </div>
      </div>
      <aside className="siderail"><SignInBox /></aside>
    </>
  );
}
