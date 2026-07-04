import { resolve } from "path";
import dotenv from "dotenv";

// Load the root .env file (ai-research-copilot/.env)
const rootEnvPath = resolve(process.cwd(), "..", ".env");
dotenv.config({ path: rootEnvPath });

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
};

export default nextConfig;
