/** @type {import("next").NextConfig} */
const config = {
  images: { unoptimized: true },
  trailingSlash: true,
  async redirects() {
    return [{ source: '/caller/:handle', destination: '/profile/:handle', permanent: true }];
  },
};
export default config;
