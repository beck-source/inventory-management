import { test, expect } from '@playwright/test'

// End-to-end coverage for the Restocking feature: budget-driven recommendations,
// order submission, and the submitted order surfacing in the Orders tab.
// Requires the dev stack running (Vite :3000 + FastAPI :8001).

test.describe('Restocking tab', () => {
  test('shows budget-driven recommendations and a summary', async ({ page }) => {
    await page.goto('/restocking')

    // Page header renders from i18n.
    await expect(page.getByRole('heading', { name: 'Restocking' })).toBeVisible()

    // The budget defaults to half of max on load, so recommendations populate immediately.
    const slider = page.locator('input[type="range"]')
    await expect(slider).toBeVisible()

    // Summary tiles are present.
    await expect(page.getByText('Total Cost')).toBeVisible()
    await expect(page.getByText('Remaining Budget')).toBeVisible()

    // At the default budget there is at least one recommended line item.
    const rows = page.locator('table tbody tr')
    await expect(rows.first()).toBeVisible()
  })

  test('maxing the budget enables Place Order and the order lands in Submitted Orders', async ({ page }) => {
    await page.goto('/restocking')

    // Push the slider to its maximum so every positive-shortfall item is recommended.
    const slider = page.locator('input[type="range"]')
    const max = await slider.getAttribute('max')
    await slider.fill(max)

    const placeOrder = page.getByRole('button', { name: 'Place Order' })
    await expect(placeOrder).toBeEnabled()
    await placeOrder.click()

    // Success banner confirms submission and exposes the generated order number.
    const banner = page.locator('.success-banner')
    await expect(banner).toBeVisible()
    const bannerText = await banner.innerText()
    const match = bannerText.match(/ORD-2025-\d{4}/)
    expect(match, 'banner should contain an ORD-2025-NNNN number').not.toBeNull()
    const orderNumber = match[0]

    // The submitted order must appear in the Orders tab under Submitted Orders.
    await page.goto('/orders')
    const submittedCard = page.locator('.card', { hasText: 'Submitted Orders' })
    await expect(submittedCard).toBeVisible()
    await expect(submittedCard.getByText(orderNumber)).toBeVisible()

    // Its row shows a lead time in days and it is NOT duplicated in the main table.
    const submittedRow = submittedCard.locator('tbody tr', { hasText: orderNumber })
    await expect(submittedRow.getByText(/\d+\s+days/)).toBeVisible()

    const allOrdersCard = page.locator('.card', { hasText: 'All Orders' })
    await expect(allOrdersCard.getByText(orderNumber)).toHaveCount(0)
  })
})
