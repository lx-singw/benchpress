import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  transpilePackages: ["@benchpress/sdk", "@benchpress/telemetry"],
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
  webpack: (config) => {
    config.externals = [...(config.externals || []), "canvas", "jsdom"];
    return config;
  },
};

export default nextConfig;
