import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const GOLD = '#c9a227';
const CREAM = '#f2ead6';
const DIM = '#5a4f35';

// Rune-U mark rebuilt from divs (Satori-safe): ring + stave + branch.
function Mark({ s = 150 }) {
  const u = s / 150;
  return (
    <div style={{
      width: s, height: s, borderRadius: '50%',
      border: `${5 * u}px solid ${GOLD}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative',
    }}>
      <div style={{ position: 'absolute', left: 44 * u, top: 34 * u,
        width: 11 * u, height: 82 * u, background: GOLD, borderRadius: 6 * u }} />
      <div style={{ position: 'absolute', left: 44 * u, top: 40 * u,
        width: 11 * u, height: 62 * u, background: GOLD, borderRadius: 6 * u,
        transform: 'rotate(-48deg)', transformOrigin: 'top center' }} />
    </div>);
}

export default function Og() {
  return new ImageResponse(
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: `6px solid ${GOLD}`, borderBottom: `6px solid ${GOLD}`,
      fontFamily: 'Georgia, serif', color: CREAM,
    }}>
      <Mark />
      <div style={{ fontSize: 64, letterSpacing: 26, marginTop: 30,
        paddingLeft: 26 }}>URDHEIM</div>
      <div style={{ fontSize: 34, fontStyle: 'italic', color: GOLD, marginTop: 14 }}>
        Every call gets a receipt.</div>
      <div style={{ fontSize: 20, letterSpacing: 8, color: DIM,
        fontFamily: 'Verdana, sans-serif', marginTop: 26, paddingLeft: 8 }}>
        SHILL RECEIPTS</div>
    </div>, { ...size });
}
