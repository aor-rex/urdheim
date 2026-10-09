const SITE = process.env.NEXT_PUBLIC_SITE || 'https://urdheim.zone.id';

export async function generateMetadata({ params }) {
  const { handle } = await params;
  const h = String(handle).toLowerCase();
  const title = '@' + h + ' · Urdheim record';
  const desc = 'Every call @' + h + ' filed, frozen at the post, judged by the chart.';
  return {
    metadataBase: new URL(SITE),
    title,
    description: desc,
    openGraph: { title, description: desc, url: SITE + '/profile/' + h, type: 'profile',
      images: [{ url: SITE + '/api/og/profile/' + h, width: 1200, height: 630 }] },
    twitter: { card: 'summary_large_image', title, description: desc,
      images: [SITE + '/api/og/profile/' + h] },
  };
}

export default function ProfileLayout({ children }) {
  return children;
}
