import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';

export default async function Og({ params }) {
  const { handle } = await params;
  let p = null;
  let s = null;
  try {
    const r = await fetch(API + '/api/profile/' + encodeURIComponent(handle),
      { next: { revalidate: 60 } });
    if (r.ok) ({ profile: p, stats: s } = await r.json());
  } catch (e) { /* fallback card below */ }
  const name = (p && p.name) || ('@' + handle);
  const filed = (s && s.filed) || 0;
  const scored = (s && s.scored) || 0;
  const avg = (s && s.avg) || 0;
  return new ImageResponse(
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: '6px solid #c9a227', borderBottom: '6px solid #c9a227',
      fontFamily: 'Georgia, serif', color: '#f2ead6',
    }}>
      <div style={{ fontSize: 26, letterSpacing: 14, color: '#5a4f35',
        fontFamily: 'Verdana, sans-serif' }}>URDHEIM · PUBLIC RECORD</div>
      <div style={{ fontSize: 84, fontStyle: 'italic', marginTop: 16 }}>{name}</div>
      <div style={{ fontSize: 30, color: '#8a7f63', fontFamily: 'Verdana, sans-serif',
        marginTop: 8 }}>@{String(handle).toLowerCase()}</div>
      <div style={{ display: 'flex', gap: 60, marginTop: 30,
        fontFamily: 'Verdana, sans-serif' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ fontSize: 56, color: '#e8e0cf' }}>{filed}</div>
          <div style={{ fontSize: 20, letterSpacing: 4, color: '#5a4f35' }}>FILED</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ fontSize: 56, color: '#e8e0cf' }}>{scored}</div>
          <div style={{ fontSize: 20, letterSpacing: 4, color: '#5a4f35' }}>SCORED</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ fontSize: 56, color: avg >= 0 ? '#7fb069' : '#c1443c' }}>
            {(avg > 0 ? '+' : '') + avg + '%'}</div>
          <div style={{ fontSize: 20, letterSpacing: 4, color: '#5a4f35' }}>AVG</div>
        </div>
      </div>
    </div>, { ...size });
}
