const SITE = process.env.NEXT_PUBLIC_SITE || 'https://urdheim.zone.id';

export default function robots() {
  return {
    rules: [{ userAgent: '*', allow: '/' }],
    sitemap: SITE + '/sitemap.xml',
  };
}
