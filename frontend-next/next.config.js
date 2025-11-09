/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // Static export for Cloudflare Pages
  images: {
    unoptimized: true // Required for static export
  },
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8001'
  }
}

module.exports = nextConfig
