import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend-Port fuer die Entwicklung. uvicorn laeuft per Default auf 8000;
// wer einen anderen Port nutzt, setzt VITE_DEV_BACKEND_PORT.
const backendPort = process.env.VITE_DEV_BACKEND_PORT ?? '8000'
const backendTarget = `http://localhost:${backendPort}`

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    // Proxy fuer die API-Endpunkte, damit das Frontend ohne hardcodierte
    // localhost-Ports auskommt (siehe src/api.ts). In Produktion uebernimmt
    // der Reverse-Proxy dieselbe Rolle. Plan Phase 1.3.
    proxy: {
      '/parse-ifc': backendTarget,
      '/validate': backendTarget,
      '/health': backendTarget,
      '/qng': backendTarget,
      '/generate-sidecar': backendTarget,
    },
  },
})
