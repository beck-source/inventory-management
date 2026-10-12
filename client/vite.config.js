import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    // fs.allow is omitted — X: is a mapped drive and path resolution
    // conflicts prevent Vite from serving files when strict mode is on.
    fs: {
      strict: false
    }
  }
})
