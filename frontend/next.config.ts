import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Environment variables that should be available in the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
