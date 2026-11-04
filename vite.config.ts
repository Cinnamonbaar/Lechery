import { defineConfig } from "vitest/config";

export default defineConfig({
  // Relative, so the build works from any subpath -- GitHub Pages today,
  // itch.io or anywhere else tomorrow.
  base: "./",
  build: {
    target: "es2020",
    // The preload polyfill alone is close to a kilobyte. Every browser we
    // target supports module preloading natively.
    modulePreload: { polyfill: false },
  },
  test: { include: ["src/**/*.test.ts"] },
});
