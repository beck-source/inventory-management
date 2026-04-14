import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('dashboard loads with KPIs and screenshot', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  await expect(page.getByText('Inventory Turnover Rate')).toBeVisible();
  await expect(page.getByText('Orders Fulfilled')).toBeVisible();
  await expect(page.getByText('Order Fill Rate')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Order Health' })).toBeVisible();
  await page.screenshot({ path: 'screenshots/dashboard.png', fullPage: true });
});

const pages = [
  { link: 'Inventory',       url: /\/inventory$/,  heading: 'Inventory' },
  { link: 'Orders',          url: /\/orders$/,     heading: 'Orders' },
  { link: 'Finance',         url: /\/spending$/,   heading: 'Finance Dashboard' },
  { link: 'Demand Forecast', url: /\/demand$/,     heading: 'Demand Forecast' },
  { link: 'Reports',         url: /\/reports$/,    heading: 'Performance Reports' },
  { link: 'Restocking',      url: /\/restocking$/, heading: 'Restocking' },
];

for (const p of pages) {
  test(`${p.link} page loads`, async ({ page }) => {
    await page.getByRole('link', { name: p.link, exact: true }).click();
    await expect(page).toHaveURL(p.url);
    await expect(page.getByRole('heading', { name: p.heading, exact: true }).first()).toBeVisible();
  });
}

test('full navigation walk-through', async ({ page }) => {
  for (const p of pages) {
    await page.getByRole('link', { name: p.link, exact: true }).click();
    await expect(page).toHaveURL(p.url);
    await expect(page.getByRole('heading', { name: p.heading, exact: true }).first()).toBeVisible();
  }
});
