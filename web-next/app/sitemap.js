const SITE = process.env.NEXT_PUBLIC_SITE || 'https://urdheim.zone.id';

export default function sitemap() {
  const now = new Date();
  return ['/', '/feed', '/leaderboard', '/coins', '/how', '/signin'].map((p) => ({
    url: SITE + p,
    lastModified: now,
  }));
}
