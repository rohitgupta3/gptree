import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../python/web/static',  // Build to backend's static folder
    emptyOutDir: true,
  },
  base: '/static/',  // Set base path for assets
})
