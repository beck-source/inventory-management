// Drives a real Chromium browser through the app to verify each navigation tab
// loads, and captures a dashboard screenshot. Equivalent to the requested
// Playwright-MCP click-through (MCP is blocked by enterprise policy here), using
// the installed @playwright/test browser instead.
//
// Assumes the dev stack is already running: Vite :3000 + FastAPI :8001.
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const BASE = 'http://localhost:3000'
const OUT = 'test-results/screenshots'
mkdirSync(OUT, { recursive: true })

// label = nav text to click; path = expected route after the click.
const TABS = [
  { label: 'Overview', path: '/' },
  { label: 'Inventory', path: '/inventory' },
  { label: 'Orders', path: '/orders' },
  { label: 'Finance', path: '/spending' },
  { label: 'Demand Forecast', path: '/demand' },
  { label: 'Restocking', path: '/restocking' },
  { label: 'Reports', path: '/reports' }
]

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

let failures = 0

// 1. Land on the dashboard and screenshot it.
await page.goto(BASE, { waitUntil: 'networkidle' })
await page.locator('.main-content h2').first().waitFor({ state: 'visible' })
await page.screenshot({ path: `${OUT}/dashboard.png`, fullPage: true })
console.log('Dashboard loaded, screenshot saved -> ' + OUT + '/dashboard.png')

// 2. Click through each nav tab and verify the route + a rendered heading.
for (const tab of TABS) {
  try {
    await page.getByRole('link', { name: tab.label, exact: true }).click()
    await page.waitForURL(`${BASE}${tab.path}`, { timeout: 5000 })

    // A loaded page shows an <h2> heading (rendered outside the loading gate).
    const heading = page.locator('.main-content h2').first()
    await heading.waitFor({ state: 'visible', timeout: 5000 })
    const title = (await heading.innerText()).trim()

    // Views start with a transient `.loading` div while data fetches async, so
    // wait for it to clear before judging. If it never clears, the page is
    // genuinely stuck loading.
    let stuckLoading = false
    try {
      await page.locator('.main-content .loading').waitFor({ state: 'hidden', timeout: 8000 })
    } catch {
      stuckLoading = true
    }
    const errorVisible = await page.locator('.main-content .error').isVisible().catch(() => false)

    const slug = tab.path === '/' ? 'root' : tab.path.slice(1)
    await page.screenshot({ path: `${OUT}/${slug}.png`, fullPage: true })

    if (errorVisible || stuckLoading) {
      failures++
      console.log(`FAIL  ${tab.label.padEnd(16)} ${tab.path} -> ${errorVisible ? 'error state' : 'stuck loading'}`)
    } else {
      console.log(`PASS  ${tab.label.padEnd(16)} ${tab.path} -> "${title}"`)
    }
  } catch (err) {
    failures++
    console.log(`FAIL  ${tab.label.padEnd(16)} ${tab.path} -> ${err.message.split('\n')[0]}`)
  }
}

await browser.close()
console.log(`\n${TABS.length - failures}/${TABS.length} tabs verified`)
process.exit(failures ? 1 : 0)
