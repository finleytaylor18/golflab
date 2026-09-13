import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Forwards API calls to the FastAPI backend during `npm run dev`, so the
    // frontend can keep using relative URLs (matching production, where
    // main.py serves this app's build directly) without needing CORS.
    proxy: {
      '/calculations': 'http://localhost:8000',
      '/clubs': 'http://localhost:8000',
      '/heads': 'http://localhost:8000',
      '/designs': 'http://localhost:8000',
    },
  },
})
