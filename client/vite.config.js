import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    // Fail instead of silently moving to 3001: the API's CORS allowlist only
    // includes port 3000, so a different port would break every request.
    strictPort: true
  }
})
