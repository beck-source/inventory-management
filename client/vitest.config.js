import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const clientDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(clientDir, '..')

export default defineConfig({
  plugins: [vue()],
  // Allow Vite's file server to serve files from the project root so that
  // test files in tests/frontend/ (outside client/) can be loaded via /@fs/.
  server: {
    fs: {
      allow: [projectRoot]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(clientDir, 'src'),
      // Explicitly resolve test-only packages to their locations in
      // client/node_modules so Vite can find them when transforming test
      // files that live outside the client/ directory tree.
      '@vue/test-utils': path.resolve(clientDir, 'node_modules/@vue/test-utils'),
      'vitest': path.resolve(clientDir, 'node_modules/vitest')
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    include: [path.join(projectRoot, 'tests/frontend/**/*.test.js')]
  }
})
