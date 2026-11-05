import { defineConfig, devices } from '@playwright/test'

// E2E config for the Vue client. Tests assume the dev stack is already running:
//   - frontend (Vite) on http://localhost:3000
//   - backend (FastAPI) on http://localhost:8001
// Start both (see CLAUDE.md "Quick Start") before `npm run test:e2e`.
export default defineConfig({
  testDir: './tests/e2e',
  // Fail fast in CI; locally surface the first broken assertion quickly.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:3000',
    // Capture artifacts only when something goes wrong, to keep runs cheap.
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ]
})
