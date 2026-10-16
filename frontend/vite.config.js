import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// in dev the api runs on :8000, in docker/k8s nginx or the ingress handles /api
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
