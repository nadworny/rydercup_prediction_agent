import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const target = process.env.ADK_API_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/apps': { target, changeOrigin: true },
      '/run_sse': { target, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test-setup.js',
  },
})
