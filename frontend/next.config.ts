import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Avoid disclosing the framework name and version in response headers.
  poweredByHeader: false,
  output: "standalone",
};

export default nextConfig;
