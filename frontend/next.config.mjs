/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001',
  },

  // API rewrites for Docker networking
  async rewrites() {
    // In Docker, proxy API requests to backend service
    // In development, use direct connection
    const isDocker = process.env.NEXT_PUBLIC_API_URL?.includes('backend:');
    
    if (isDocker) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://backend:5001/api/:path*',
        },
      ];
    }
    
    return [];
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
