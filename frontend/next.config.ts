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
  // /api/* is proxied by the runtime route handler in
  // src/app/api/[...path]/route.ts rather than a rewrite here. Rewrites
  // resolve their destination at build time, which made API_URL a build-time
  // input — wrong for both ECS (where it is a task env var) and Vercel.
}

export default nextConfig
