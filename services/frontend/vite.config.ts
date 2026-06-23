import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
      "/health": "http://localhost:8000",
      "/openmetadata": {
        target: "http://localhost:8585",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/openmetadata/, ""),
      },
    },
  },
  build: { outDir: "dist" },
});
