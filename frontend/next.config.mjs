/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001',
  },

  // Optimize images
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },

  // Enable React strict mode
  reactStrictMode: true,

  // Disable x-powered-by header
  poweredByHeader: false,

  // Experimental features
  experimental: {
    // Enable server actions
  },
};

export default nextConfig;
