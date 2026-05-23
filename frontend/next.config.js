/** @type {import('next').NextConfig} */

const isDev = process.env.NODE_ENV === 'development';
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  async rewrites() {
    if (isDev) {
      return [
        { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
        { source: '/exports/:path*', destination: 'http://localhost:8000/exports/:path*' },
      ];
    }
    return [];
  },
  output: 'standalone',
};

module.exports = nextConfig;
