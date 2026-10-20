import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// En desarrollo Vite inyecta scripts inline (HMR), por eso la CSP solo se aplica al build.
const CSP =
  "default-src 'self'; img-src 'self' blob: data: https://images.pexels.com; media-src 'self' blob:; " +
  "style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'";

const cspForBuild = (): Plugin => ({
  name: "csp-for-build",
  apply: "build",
  transformIndexHtml: () => [
    { tag: "meta", attrs: { "http-equiv": "Content-Security-Policy", content: CSP }, injectTo: "head-prepend" },
  ],
});

export default defineConfig({
  plugins: [react(), cspForBuild()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
