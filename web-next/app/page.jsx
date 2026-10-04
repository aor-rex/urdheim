import { X_URL } from '../lib/data';

export default function Home() {
  return (
    <div className="wrap">
      <div style={{ textAlign: 'center', padding: '90px 0 60px' }}>
        <div className="eyebrow">THE ETERNAL RECORD</div>
        <h1 style={{ fontSize: 76, letterSpacing: 12, margin: '16px 0 6px', fontWeight: 400 }}>URDHEIM</h1>
        <div style={{ fontStyle: 'italic', color: '#9a8c6c', fontSize: 19 }}>crypto callers, held to account.</div>
        <p style={{ color: '#8a7f63', maxWidth: 560, margin: '22px auto 0', lineHeight: 1.7, fontSize: 16 }}>
          When a caller posts a coin, we snapshot the price. When it rugs, the receipt is already written.
          No arguments, no deleted tweets — just the record.
        </p>
        <div className="sans" style={{ display: 'flex', gap: 14, justifyContent: 'center', marginTop: 34 }}>
          <a href="/leaderboard" style={{ padding: '14px 34px', fontSize: 13, letterSpacing: 2, textDecoration: 'none', borderRadius: 3, background: '#c9a227', color: '#0c0a08', fontWeight: 700 }}>VIEW THE LEADERBOARD</a>
          <a href="/snitch" style={{ padding: '14px 34px', fontSize: 13, letterSpacing: 2, textDecoration: 'none', borderRadius: 3, border: '1px solid #4a4132', color: '#b7a67f' }}>SNITCH A CALL</a>
        </div>
      </div>

      <div className="sans" style={{ display: 'flex', borderTop: '1px solid #2b2519', borderBottom: '1px solid #2b2519', margin: '10px 0 60px' }}>
        {[['132', 'CALLERS TRACKED'], ['1,408', 'CALLS ON RECORD'], ['311', 'RUGS CAUGHT'], ['0', 'RECEIPTS DELETED']].map(([b, s], i, a) => (
          <div key={s} style={{ flex: 1, textAlign: 'center', padding: '26px 10px', borderRight: i < a.length - 1 ? '1px solid #2b2519' : 'none' }}>
            <b style={{ display: 'block', fontSize: 34, color: '#c9a227', fontWeight: 400, fontFamily: 'Georgia,serif' }}>{b}</b>
            <span style={{ fontSize: 11, letterSpacing: 2, color: '#8a7f63' }}>{s}</span>
          </div>
        ))}
      </div>

      <h2 className="sans" style={{ fontSize: 15, letterSpacing: 5, color: '#c9a227', fontWeight: 400, marginBottom: 26, textAlign: 'center' }}>HOW THE RECORD IS WRITTEN</h2>
      <div style={{ display: 'flex', gap: 14, marginBottom: 70 }}>
        {[['i.', 'The watcher sees', 'Every tracked caller is polled around the clock. A coin address in a post gets flagged in minutes.'],
          ['ii.', 'The price is frozen', 'Price and market cap at the moment of the call — before the chart moves, before the story changes.'],
          ['iii.', 'The verdict lands', 'Green or red, with the original post linked. The caller page updates. Heimdall posts the worst of it daily.']].map(([n, h, p]) => (
          <div key={n} style={{ flex: 1, border: '1px solid #2b2519', borderRadius: 4, padding: '26px 22px', background: '#121009' }}>
            <div style={{ fontStyle: 'italic', fontSize: 28, color: '#5a4f35' }}>{n}</div>
            <h3 style={{ fontSize: 19, margin: '10px 0 8px', fontWeight: 400 }}>{h}</h3>
            <p style={{ fontSize: 14, color: '#9a8c6c', lineHeight: 1.65, fontStyle: 'italic' }}>{p}</p>
          </div>
        ))}
      </div>

      <h2 className="sans" style={{ fontSize: 15, letterSpacing: 5, color: '#c9a227', fontWeight: 400, marginBottom: 26, textAlign: 'center' }}>WORST CALL THIS WEEK</h2>
      <div style={{ border: '1px solid #c1443c', borderRadius: 4, padding: 28, marginBottom: 70, background: '#150d0c' }}>
        <div className="sans" style={{ fontSize: 11, letterSpacing: 3, color: '#c1443c' }}>FILED BY HEIMDALL · OCT 2</div>
        <h3 style={{ fontSize: 26, margin: '10px 0 6px', fontWeight: 400 }}>@pumporacle called $DUMP</h3>
        <p style={{ fontStyle: 'italic', color: '#b7a67f', lineHeight: 1.7 }}>“Last chance to enter, this one is different.” It was not different.</p>
        <div className="sans" style={{ display: 'flex', gap: 30, marginTop: 16, fontSize: 13 }}>
          <span><b className="rd" style={{ display: 'block', fontSize: 22, fontFamily: 'Georgia,serif' }}>$0.041 → $0.00008</b>price then → now</span>
          <span><b className="rd" style={{ display: 'block', fontSize: 22, fontFamily: 'Georgia,serif' }}>−99.8%</b>return</span>
          <span><b className="rd" style={{ display: 'block', fontSize: 22, fontFamily: 'Georgia,serif' }}>4 hrs</b>to zero</span>
        </div>
      </div>

      <div style={{ textAlign: 'center', border: '1px solid #2b2519', borderRadius: 4, padding: 44, marginBottom: 30, background: '#121009' }}>
        <div className="eyebrow">DAILY FLOPS · RUG SIRENS · FRIDAY RECAPS</div>
        <p style={{ fontStyle: 'italic', color: '#9a8c6c', margin: '10px 0 22px' }}>Heimdall posts the worst of the record every day. Follow or stay gullible.</p>
        <a className="sans" href={X_URL} style={{ fontSize: 13, letterSpacing: 2, color: '#0c0a08', background: '#f2ead6', padding: '13px 32px', textDecoration: 'none', borderRadius: 3, fontWeight: 700 }}>FOLLOW @URDHEIM</a>
      </div>
    </div>
  );
}
