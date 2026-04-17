/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'frontend',  // Avoid 'out' which vmux excludes by default
  reactStrictMode: false,
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
