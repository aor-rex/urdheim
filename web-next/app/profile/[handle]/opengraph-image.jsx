import { ImageResponse } from 'next/og';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const GOLD = '#c9a227';
const CREAM = '#f2ead6';
const DIM = '#5a4f35';
const FAINT = '#8a7f63';
const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';

async function font(name) {
  const b = await readFile(join(process.cwd(), 'app', 'og-fonts', name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

// X avatar -> data URI so the card never depends on hotlinking.
async function avatar(url) {
  try {
    const r = await fetch(url.replace('_normal.', '_400x400.'),
      { signal: AbortSignal.timeout(7000) });
    if (!r.ok) throw new Error('no pic');
    const b = Buffer.from(await r.arrayBuffer());
    return `data:image/jpeg;base64,${b.toString('base64')}`;
  } catch (e) {
    return null;
  }
}

function Stat({ v, label, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontSize: 64, color: color || CREAM }}>{v}</div>
      <div style={{ fontSize: 19, letterSpacing: 5, color: DIM,
        fontFamily: 'Verdana, sans-serif', marginTop: 6 }}>{label}</div>
    </div>);
}

export default async function Og({ params }) {
  const { handle } = await params;
  const h = String(handle).toLowerCase();
  let p = null;
  let s = null;
  try {
    const r = await fetch(API + '/api/profile/' + encodeURIComponent(h),
      { next: { revalidate: 60 }, signal: AbortSignal.timeout(7000) });
    if (r.ok) ({ profile: p, stats: s } = await r.json());
  } catch (e) { /* fallback card below */ }
  const name = (p && p.name) || ('@' + h);
  const pic = p && p.avatar ? await avatar(p.avatar) : null;
  const filed = (s && s.filed) || 0;
  const scored = (s && s.scored) || 0;
  const avg = (s && s.avg) || 0;
  const avgC = avg > 0 ? '#7fb069' : avg < 0 ? '#c1443c' : CREAM;
  const [reg, ita, sans] = await Promise.all([
    font('Gelasio-Regular.ttf'),
    font('Gelasio-Italic.ttf'),
    font('LiberationSans-Regular.ttf'),
  ]);
  return new ImageResponse(
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: `6px solid ${GOLD}`, borderBottom: `6px solid ${GOLD}`,
      fontFamily: 'Georgia, serif', color: CREAM,
    }}>
      <div style={{ fontSize: 22, letterSpacing: 12, color: DIM,
        fontFamily: 'Verdana, sans-serif', paddingLeft: 12 }}>
        URDHEIM · PUBLIC RECORD</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 44, marginTop: 34 }}>
        {pic
          ? <img src={pic} width={150} height={150}
              style={{ borderRadius: '50%', border: `4px solid ${GOLD}` }} />
          : <div style={{ width: 150, height: 150, borderRadius: '50%',
              border: `4px solid ${GOLD}`, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 64, color: GOLD }}>
              {h.slice(0, 1).toUpperCase()}</div>}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: 72, fontStyle: 'italic' }}>{name}</div>
          <div style={{ fontSize: 28, color: FAINT,
            fontFamily: 'Verdana, sans-serif', marginTop: 6 }}>@{h}</div>
        </div>
        <div style={{ width: 2, height: 170, background: '#2b2519', margin: '0 8px' }} />
        <div style={{ display: 'flex', gap: 54 }}>
          <Stat v={filed} label="FILED" />
          <Stat v={scored} label="SCORED" />
          <Stat v={(avg > 0 ? '+' : '') + avg + '%'} label="AVG RETURN" color={avgC} />
        </div>
      </div>
    </div>, {
      ...size,
      fonts: [
        { name: 'Georgia', data: reg, style: 'normal', weight: 400 },
        { name: 'Georgia', data: ita, style: 'italic', weight: 400 },
        { name: 'Verdana', data: sans, style: 'normal', weight: 400 },
      ],
    });
}
