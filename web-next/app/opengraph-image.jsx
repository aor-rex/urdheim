import { ImageResponse } from 'next/og';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const GOLD = '#c9a227';
const CREAM = '#f2ead6';
const DIM = '#5a4f35';

async function asset(name) {
  const b = await readFile(join(process.cwd(), 'public', name));
  return `data:image/png;base64,${b.toString('base64')}`;
}

async function font(name) {
  const b = await readFile(join(process.cwd(), 'app', 'og-fonts', name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

export default async function Og() {
  const [logo, reg, ita] = await Promise.all([
    asset('logo-og.png'),
    font('Gelasio-Regular.ttf'),
    font('Gelasio-Italic.ttf'),
  ]);
  return new ImageResponse(
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: `6px solid ${GOLD}`, borderBottom: `6px solid ${GOLD}`,
      fontFamily: 'Georgia, serif', color: CREAM,
    }}>
      <img src={logo} width={150} height={150} />
      <div style={{ fontSize: 64, letterSpacing: 26, marginTop: 30,
        paddingLeft: 26 }}>URDHEIM</div>
      <div style={{ display: 'flex', fontSize: 34, fontStyle: 'italic',
        color: GOLD, marginTop: 14 }}>
        <span>Every call gets a receipt.</span></div>
      <div style={{ fontSize: 20, letterSpacing: 8, color: DIM,
        fontFamily: 'Verdana, sans-serif', marginTop: 26, paddingLeft: 8 }}>
        SHILL RECEIPTS</div>
    </div>, {
      ...size,
      fonts: [
        { name: 'Georgia', data: reg, style: 'normal', weight: 400 },
        { name: 'Georgia', data: ita, style: 'italic', weight: 400 },
      ],
    });
}
