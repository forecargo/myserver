import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const isProd = process.env.NODE_ENV === "production";

export default defineConfig({
  plugins: [react()],
  base: isProd ? "/mermaid/" : "/",
  server: {
    proxy: {
      "/api": "http://localhost:8004",
    },
  },
});
