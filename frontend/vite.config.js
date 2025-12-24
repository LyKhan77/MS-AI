import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Exposes to network (0.0.0.0)
    proxy: {
      '/api': {
        target: 'http://192.168.2.132:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://192.168.2.132:5000',
        ws: true
      }
    }
  }
})
