import type { NextConfig } from "next";

// Import configuration for consistent API path management
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';

const nextConfig: NextConfig = {
  eslint: {
    // Enable ESLint during builds for production quality
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Enable type checking during builds for production quality
    ignoreBuildErrors: false,
  },
  // Enable standalone output for Docker
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${API_URL}${API_PREFIX}/:path*`,
      },
      // Health check endpoint for Docker
      {
        source: '/api/health',
        destination: '/api/health',
      },
    ];
  },
  // Configure headers for Docker environment
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
