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
    openGraph: { title, description: desc, url: SITE + '/profile/' + h, type: 'profile' },
    twitter: { card: 'summary_large_image', title, description: desc },
  };
}

export default function ProfileLayout({ children }) {
  return children;
}
