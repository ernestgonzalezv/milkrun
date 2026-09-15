import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Config unica para Vite y Vitest: `defineConfig` de vitest/config es el
// mismo de Vite mas la clave `test`, asi no hay dos archivos que sincronizar.
export default defineConfig({
  plugins: [react()],

  optimizeDeps: {
    // MapLibre 6 ships its Web Worker as a sibling file and resolves it with
    // `new URL('./maplibre-gl-worker.mjs', import.meta.url)`. Pre-bundling
    // rewrites that module into node_modules/.vite/deps/, where the worker
    // file does not exist, so the URL 404s. MapLibre swallows that in a catch
    // and simply never requests a tile: the style loads, `load` never fires,
    // and the map sits there looking like a slow network.
    //
    // Excluding it makes Vite serve the real ESM from node_modules, where the
    // sibling resolves. Only affects dev — the production build resolves the
    // worker correctly on its own.
    exclude: ['maplibre-gl'],
  },
  server: {
    // El dashboard llama a rutas relativas (/api/...) y el dev server hace de
    // proxy. Asi el navegador nunca ve un origen distinto y CORS deja de
    // existir en desarrollo. En produccion sirve el mismo dominio o se
    // configura VITE_API_URL.
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    css: false,
  },
})
