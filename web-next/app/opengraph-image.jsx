import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

function Shell({ children }) {
  return (
    <div style={{
      width: 1200, height: 630, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0c0a08',
      borderTop: '6px solid #c9a227', borderBottom: '6px solid #c9a227',
      fontFamily: 'Georgia, serif', color: '#f2ead6',
    }}>
      <div style={{ fontSize: 26, letterSpacing: 14, color: '#5a4f35',
        fontFamily: 'Verdana, sans-serif' }}>URDHEIM</div>
      {children}
      <div style={{ fontSize: 22, letterSpacing: 6, color: '#5a4f35',
        fontFamily: 'Verdana, sans-serif', marginTop: 28 }}>
        SHILL RECEIPTS · SOLANA + ROBINHOOD CHAIN</div>
    </div>);
}

export default function Og() {
  return new ImageResponse(
    <Shell>
      <div style={{ fontSize: 96, fontStyle: 'italic', marginTop: 20, display: 'flex' }}>
        <span>Every call gets a&nbsp;</span><span style={{ color: '#c9a227' }}>receipt</span><span>.</span></div>
    </Shell>, { ...size });
}
