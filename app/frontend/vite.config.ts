import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy /api to the backend so the frontend never needs CORS config.
// In the cluster, ingress-nginx does the same path-based routing (Phase 2).
// VITE_API_PROXY_TARGET lets docker-compose point this at the "backend"
// container by its service name instead of localhost.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
