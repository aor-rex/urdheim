import { ImageResponse } from 'next/og';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const GOLD = '#c9a227';
const CREAM = '#f2ead6';
const DIM = '#5a4f35';
const FAINT = '#8a7f63';
const GREEN = '#7fb069';
const RED = '#c1443c';
const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8091';

export const runtime = 'nodejs';

async function font(name) {
  const b = await readFile(join(process.cwd(), 'app', 'og-fonts', name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

function fmtMcap(n) {
  if (!n) return '$0';
  if (n >= 1000000000) return '$' + (n / 1000000000).toFixed(2) + 'B';
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(2) + 'M';
  if (n >= 1000) return '$' + (n / 1000).toFixed(1).replace('.0', '') + 'K';
  return '$' + String(Math.round(n));
}

function Stat({ v, label, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontSize: 52, color: color || CREAM }}>{v}</div>
      <div style={{ fontSize: 17, letterSpacing: 5, color: DIM,
        fontFamily: 'Verdana, sans-serif', marginTop: 6 }}>{label}</div>
    </div>);
}

export default async function Og({ params }) {
  const { mint } = (await params) || {};
  const id = String(mint || '');
  let c = null;
  try {
    const [reg, ita, sans] = await Promise.all([
      font('Gelasio-Regular.ttf'),
      font('Gelasio-Italic.ttf'),
      font('LiberationSans-Regular.ttf'),
    ]);
    try {
      const r = await fetch(API + '/api/coin/' + encodeURIComponent(id),
        { next: { revalidate: 60 }, signal: AbortSignal.timeout(2500) });
      if (r.ok) c = await r.json();
    } catch (e) { /* numbers stay blank, card still renders */ }
    return new ImageResponse(card(c, id), {
      ...size,
      fonts: [
        { name: 'Georgia', data: reg, style: 'normal', weight: 400 },
        { name: 'Georgia', data: ita, style: 'italic', weight: 400 },
        { name: 'Verdana', data: sans, style: 'normal', weight: 400 },
      ],
    });
  } catch (e) {
    return new ImageResponse(card(null, id), { ...size });
  }
}

function card(c, id) {
  const ticker = (c && c.coin) || 'UNKNOWN';
  const seal = c && c.dead ? 'RUGGED' : 'TRACKED';
  const sealC = c && c.dead ? RED : GOLD;
  const n = (c && c.touchers && c.touchers.length) || 0;
  return (
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: `6px solid ${GOLD}`, borderBottom: `6px solid ${GOLD}`,
      fontFamily: 'Georgia, serif', color: CREAM,
    }}>
      <div style={{ fontSize: 22, letterSpacing: 12, color: DIM,
        fontFamily: 'Verdana, sans-serif', paddingLeft: 12 }}>
        URDHEIM · SHILL RECEIPT</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 40,
        marginTop: 30, maxWidth: 1104 }}>
        <div style={{ display: 'flex', flexDirection: 'column', maxWidth: 480,
          overflow: 'hidden' }}>
          <div style={{ fontSize: 84, whiteSpace: 'nowrap',
            overflow: 'hidden', textOverflow: 'ellipsis' }}>${ticker}</div>
          <div style={{ fontSize: 24, color: sealC,
            fontFamily: 'Verdana, sans-serif', marginTop: 10,
            letterSpacing: 4 }}>{seal} {c ? c.delta : ''}</div>
        </div>
        <div style={{ width: 2, height: 170, background: '#2b2519', flex: 'none' }} />
        <div style={{ display: 'flex', gap: 44, flex: 'none' }}>
          <Stat v={fmtMcap(c && c.peak)} label="PEAK MCAP" />
          <Stat v={fmtMcap(c && c.now)} label="NOW MCAP"
            color={c && c.now < c.peak ? RED : GREEN} />
          <Stat v={n} label={n === 1 ? 'CALLER' : 'CALLERS'} color={GOLD} />
        </div>
      </div>
      <div style={{ fontSize: 20, color: FAINT, marginTop: 34,
        fontFamily: 'Verdana, sans-serif', letterSpacing: 1 }}>
        {id.slice(0, 18) + '...' + id.slice(-6) + ' · urdheim.zone.id'}</div>
    </div>);
}
