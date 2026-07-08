import type { NextConfig } from "next";

const allowedDevOrigins = process.env.ALLOWED_DEV_ORIGINS
  ? process.env.ALLOWED_DEV_ORIGINS.split(",")
  : ["localhost"];

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins,
};

export default nextConfig;
