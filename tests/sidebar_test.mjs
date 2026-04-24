import { chromium } from '/opt/homebrew/lib/node_modules/playwright/index.mjs';
import { existsSync, mkdirSync } from 'fs';
import path from 'path';

const SCREENSHOTS_DIR = '/Users/mtaczynski/repos/inventory-management/tests/screenshots';
if (!existsSync(SCREENSHOTS_DIR)) mkdirSync(SCREENSHOTS_DIR, { recursive: true });

const shot = (page, name) => page.screenshot({ path: path.join(SCREENSHOTS_DIR, name), fullPage: false });

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const results = [];
  const log = (label, details) => { results.push({ label, details }); console.log(`[${label}]`, details); };

  // ── Step 1: Initial load ──────────────────────────────────────────────────
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await shot(page, '01_initial.png');

  const sidebar = await page.locator('.sidebar');
  const sidebarVisible = await sidebar.isVisible();
  const sidebarBg = await sidebar.evaluate(el => getComputedStyle(el).backgroundColor);
  const sidebarWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);
  const isCollapsed = await sidebar.evaluate(el => el.classList.contains('collapsed'));

  const navLinks = await page.locator('.sidebar-nav a').all();
  const navLabels = [];
  for (const link of navLinks) {
    const label = await link.locator('.nav-label').textContent();
    navLabels.push(label.trim());
  }

  const headerVisible = await page.locator('.top-nav').isVisible();
  const logoVisible = await page.locator('.logo').isVisible();
  const filterBarVisible = await page.locator('.filter-bar, .filters, select').first().isVisible();
  const profileVisible = await page.locator('.profile-menu, [class*="profile"]').first().isVisible();
  const langSwitcherVisible = await page.locator('.lang-switcher, .language-switcher, [class*="lang"]').first().isVisible();

  log('Step 1 - Initial Load', {
    sidebarVisible,
    sidebarBg,
    sidebarWidth: Math.round(sidebarWidth),
    isCollapsed,
    navLabels,
    navCount: navLabels.length,
    headerVisible,
    logoVisible,
    filterBarVisible,
    profileVisible,
    langSwitcherVisible
  });

  // ── Step 2: Collapse sidebar ──────────────────────────────────────────────
  const toggleBtn = await page.locator('.sidebar-toggle');
  await toggleBtn.click();
  await page.waitForTimeout(400); // allow CSS transition
  await shot(page, '02_collapsed.png');

  const sidebarWidthAfterCollapse = await sidebar.evaluate(el => el.getBoundingClientRect().width);
  const isCollapsedAfter = await sidebar.evaluate(el => el.classList.contains('collapsed'));
  const mainMargin = await page.locator('.app-main').evaluate(el => getComputedStyle(el).marginLeft);
  const iconsVisible = await page.locator('.sidebar-nav .nav-icon').first().isVisible();
  const labelsHidden = await page.locator('.sidebar-nav .nav-label').first().evaluate(el => getComputedStyle(el).opacity);

  log('Step 2 - Collapsed Sidebar', {
    sidebarWidthAfterCollapse: Math.round(sidebarWidthAfterCollapse),
    isCollapsedAfter,
    mainMargin,
    iconsVisible,
    labelOpacity: labelsHidden
  });

  // ── Step 3: Re-expand sidebar ─────────────────────────────────────────────
  await toggleBtn.click();
  await page.waitForTimeout(400);
  await shot(page, '03_expanded_again.png');

  const sidebarWidthExpanded = await sidebar.evaluate(el => el.getBoundingClientRect().width);
  const isExpandedAgain = !await sidebar.evaluate(el => el.classList.contains('collapsed'));

  log('Step 3 - Re-expanded Sidebar', {
    sidebarWidthExpanded: Math.round(sidebarWidthExpanded),
    isExpandedAgain
  });

  // ── Step 4: Click Inventory ───────────────────────────────────────────────
  const inventoryLink = await page.locator('.sidebar-nav a[href="/inventory"]');
  await inventoryLink.click();
  await page.waitForTimeout(800);
  await shot(page, '04_inventory_active.png');

  const currentUrl = page.url();
  const inventoryActive = await inventoryLink.evaluate(el => el.classList.contains('active'));
  const inventoryBg = await inventoryLink.evaluate(el => getComputedStyle(el).backgroundColor);

  log('Step 4 - Inventory Navigation', {
    currentUrl,
    inventoryActive,
    inventoryBg
  });

  // ── Step 5: Click Restocking ──────────────────────────────────────────────
  const restockingLink = await page.locator('.sidebar-nav a[href="/restocking"]');
  await restockingLink.click();
  await page.waitForTimeout(800);
  await shot(page, '05_restocking.png');

  const restockingUrl = page.url();
  const restockingActive = await restockingLink.evaluate(el => el.classList.contains('active'));
  const pageHeading = await page.locator('h2, .page-header h2').first().textContent().catch(() => 'N/A');

  log('Step 5 - Restocking Navigation', {
    restockingUrl,
    restockingActive,
    pageHeading
  });

  // ── Step 6: Narrow viewport (900px) ──────────────────────────────────────
  await context.newPage(); // not needed, resize on current
  await page.setViewportSize({ width: 900, height: 900 });
  await page.waitForTimeout(600);
  await shot(page, '06_narrow_900px.png');

  const sidebarWidthNarrow = await sidebar.evaluate(el => el.getBoundingClientRect().width);
  const isCollapsedNarrow = await sidebar.evaluate(el => el.classList.contains('collapsed'));

  log('Step 6 - 900px Viewport', {
    sidebarWidthNarrow: Math.round(sidebarWidthNarrow),
    isCollapsedNarrow
  });

  // ── Summary ───────────────────────────────────────────────────────────────
  console.log('\n=== FULL RESULTS ===');
  results.forEach(r => {
    console.log(`\n--- ${r.label} ---`);
    console.log(JSON.stringify(r.details, null, 2));
  });

  await browser.close();
})();
