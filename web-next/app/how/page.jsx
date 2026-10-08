import { SignInBox } from '../../lib/components';

const STEPS = [
  ['1. Tag the call', 'Reply to any call post with @urdheim, or tag us with a coin address. That tag is your filing.'],
  ['2. The detective reads it', 'Every tagged post gets read and judged: real call, soft shill, or just chatting. Only real calls enter the record.'],
  ['3. The price freezes', 'Entry price and market cap snapshot at the moment of the call, before the chart moves and the story changes.'],
  ['4. The verdict lands', 'The snapshotter reprices open calls. Green holds, red condemns. The receipt updates itself.'],
];

export default function How() {
  return (
    <>
      <div className="feedcol">
        <div className="fhead">
          <h1>Help</h1>
          <div className="sub">Four steps between a shill and a verdict.</div>
        </div>
        <div style={{ padding: '8px 28px 0' }}>
          {STEPS.map(([h, p]) => (
            <div key={h} style={{ padding: '22px 0', borderBottom: '1px solid #2b2519' }}>
              <h2 style={{ fontSize: 21, fontWeight: 400, color: '#c9a227' }}>{h}</h2>
              <p style={{ fontSize: 15.5, color: '#9a8c6c', lineHeight: 1.7, marginTop: 8 }}>{p}</p>
            </div>))}
          <p style={{ fontSize: 15.5, color: '#8a7f63', lineHeight: 1.7, padding: '22px 0' }}>
            No account needed to file. Sign in only when you want the filings tied to your name,
            on your public record.</p>
        </div>
      </div>
      <aside className="siderail"><SignInBox /></aside>
    </>
  );
}
