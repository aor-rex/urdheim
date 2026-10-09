const SITE = process.env.NEXT_PUBLIC_SITE || 'https://urdheim.zone.id';

export async function generateMetadata({ params }) {
  const { mint } = await params;
  const id = String(mint);
  const title = 'Coin record · Urdheim';
  const desc = 'Peak vs now in mcap, every tracked caller who touched it.';
  return {
    metadataBase: new URL(SITE),
    title,
    description: desc,
    openGraph: {
      title, description: desc, url: SITE + '/coin/' + id,
      type: 'website',
      images: [{ url: SITE + '/api/og/coin/' + id, width: 1200, height: 630 }],
    },
    twitter: {
      card: 'summary_large_image', title, description: desc,
      images: [SITE + '/api/og/coin/' + id],
    },
  };
}

export default function CoinLayout({ children }) {
  return children;
}
