import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // "standalone" produces the self-contained server.js the Docker image runs.
  // Vercel builds its own output format, so skip it there.
  output: process.env.VERCEL ? undefined : "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
