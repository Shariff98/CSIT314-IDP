import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Development: React runs on :5173 and Flask on :5000. The React pages use #/ addresses, so
// every real path below belongs to Flask: the JSON API, uploaded photos, and the Flask
// pages that admins, platform managers and the designer's full analytics use.
const FLASK = { target: 'http://127.0.0.1:5000', changeOrigin: true };
const FLASK_PATHS = ['/api', '/uploads', '/admin', '/platform', '/analytics', '/logout'];

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(FLASK_PATHS.map((path) => [path, FLASK])),
  },
});
