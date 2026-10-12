import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// dev: proxy /api -> backend (uvicorn :9010) เพื่อเลี่ยง CORS ระหว่างพัฒนา
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:9010',
        changeOrigin: true,
      },
    },
  },
})
