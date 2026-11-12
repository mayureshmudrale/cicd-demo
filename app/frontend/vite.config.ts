import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy /api to the backend so the frontend never needs CORS config.
// In the cluster, ingress-nginx does the same path-based routing (Phase 2).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
