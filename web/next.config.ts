import path from "path";

import type { NextConfig } from "next";

const basePath = "/horn-ok-please";
const liveMode = process.env.NEXT_PUBLIC_LIVE_MODE === "1";

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  assetPrefix: basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  webpack: (config, { webpack }) => {
    if (liveMode) {
      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(
          /[\\/]live-dialog-gate(\.tsx)?$/,
          path.join(process.cwd(), "src/components/live-dialog-on.tsx"),
        ),
      );
    } else {
      config.plugins.push(
        new webpack.IgnorePlugin({
          resourceRegExp: /[\\/]live-dialog(\.tsx)?$/,
        }),
      );
    }
    return config;
  },
};

export default nextConfig;
