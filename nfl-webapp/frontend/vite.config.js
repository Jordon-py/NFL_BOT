/* vite.config.js
 * Teaching goal:
 * - Proxy /api/* to the FastAPI backend on :8000 so fetch('/api/predict') "just works".
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000"
    }
  }
});
