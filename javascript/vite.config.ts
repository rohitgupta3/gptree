import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  build: {
    outDir: "../python/web/static", // Build to backend's static folder
    emptyOutDir: true,
  },
  // Only use /static/ base in production builds
  base: command === "build" ? "/static/" : "/",
}));
