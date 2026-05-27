/** @type {import('next').NextConfig} */

const isDev = process.env.NODE_ENV === 'development';

const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  // Dev 模式不用 output: export，否则 SSR 会报错
  ...(!isDev && { distDir: '../static_export', output: 'export' }),
};

// Dev-only: proxy API requests to backend
if (isDev) {
  nextConfig.rewrites = async () => [
    { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
    { source: '/exports/:path*', destination: 'http://localhost:8000/exports/:path*' },
  ];
}

module.exports = nextConfig;
