import './globals.css';
import Nav from './nav';

export const metadata = { title: 'Urdheim — every call leaves a record' };

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ paddingBottom: 60 }}>
        <Nav />
        {children}
        <footer>
          <span>URDHEIM — what is written cannot be unwritten</span>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 24 }}>
            <a href="/leaderboard">LEADERBOARD</a>
            <a href="/snitch">SNITCH</a>
            <a href="https://x.com/Urdheim">X ACCOUNT</a>
          </span>
        </footer>
      </body>
    </html>
  );
}
