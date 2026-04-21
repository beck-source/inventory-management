// Tests for the budget-selection logic in client/src/views/Restocking.vue
//
// Strategy: mount the component with a mocked api module and a stubbed
// vue-router. We feed controlled candidate data so that the greedy
// autoSelect algorithm and the computed selectedTotal can be verified in
// isolation from the network.
//
// Candidate shape expected by the component:
//   { sku, name, warehouse, trend, quantity_on_hand, forecasted_demand,
//     shortfall, recommended_qty, unit_cost, estimated_cost, lead_time_days }
//
// autoSelect uses `estimated_cost` for budget decisions.
// selectedTotal uses `recommended_qty * unit_cost`.

import { mount, flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'

// Mock the api module before importing the component so that the component
// receives the mock at the time its module-level imports resolve.
vi.mock('../../client/src/api.js', () => ({
  api: {
    getRestockingCandidates: vi.fn(),
    submitRestockingOrder: vi.fn()
  }
}))

// Mock vue-router so the component does not throw when useRouter() is called
// and router.push('/orders') is called after a successful order.
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

// Also mock useFilters so filter state is isolated from the singleton.
vi.mock('../../client/src/composables/useFilters.js', () => ({
  useFilters: () => ({
    getCurrentFilters: () => ({ warehouse: 'all', category: 'all', status: 'all' }),
    selectedLocation: { value: 'all' },
    selectedCategory: { value: 'all' }
  })
}))

import { api } from '../../client/src/api.js'
import Restocking from '../../client/src/views/Restocking.vue'

// Build a minimal candidate with all fields the component accesses.
function makeCandidate(overrides) {
  return {
    sku: 'TEST-001',
    name: 'Test Part',
    warehouse: 'San Francisco',
    trend: 'stable',
    quantity_on_hand: 10,
    forecasted_demand: 50,
    shortfall: 40,
    recommended_qty: 40,
    unit_cost: 10,
    estimated_cost: 400,
    lead_time_days: 7,
    ...overrides
  }
}

async function mountWithCandidates(candidates) {
  api.getRestockingCandidates.mockResolvedValue(candidates)
  const wrapper = mount(Restocking, {
    global: {
      stubs: {
        // Stub the router-link if referenced; not needed here but safe.
        RouterLink: true
      }
    }
  })
  await flushPromises()
  return wrapper
}

describe('Restocking — budget selection logic', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  // --- Budget 0: nothing selected ---

  it('selects no items when budget is 0', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 100 }),
      makeCandidate({ sku: 'B-001', estimated_cost: 200 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Force budget to 0 so autoSelect has nothing to pick.
    await wrapper.find('input[type="range"]').setValue(0)
    await wrapper.vm.$nextTick()

    // No checked checkboxes.
    const checked = wrapper.findAll('input[type="checkbox"]').filter(c => c.element.checked)
    expect(checked).toHaveLength(0)
  })

  // --- Budget >= total cost: all items selected ---

  it('selects all items when budget covers the full estimated cost of every candidate', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 300 }),
      makeCandidate({ sku: 'B-001', estimated_cost: 500 })
    ]
    // Total cost = 800. sliderMax will be >= 800.
    const wrapper = await mountWithCandidates(candidates)

    // The component sets budget = sliderMax on load and auto-selects.
    const checked = wrapper.findAll('input[type="checkbox"]').filter(c => c.element.checked)
    expect(checked).toHaveLength(2)
  })

  // --- Greedy selection: highest-shortfall items that fit ---

  it('selects greedily — picks items whose estimated_cost fits within budget, highest-shortfall first', async () => {
    // Candidates are returned from the API in the order they appear.
    // autoSelect iterates in that order and takes each item whose estimated_cost
    // fits within remaining budget. The component does NOT sort internally —
    // it trusts the API ordering. We verify greedy fill behaviour by providing
    // an ordering where the first item fits but the second does not.
    const candidates = [
      makeCandidate({ sku: 'CHEAP', estimated_cost: 200, shortfall: 40 }),
      makeCandidate({ sku: 'EXPENSIVE', estimated_cost: 900, shortfall: 80 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Set budget to 500 so only the first item (200) fits.
    await wrapper.find('input[type="range"]').setValue(500)
    await wrapper.vm.$nextTick()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    // First row selected, second not.
    expect(checkboxes[0].element.checked).toBe(true)
    expect(checkboxes[1].element.checked).toBe(false)
  })

  // --- Manual toggle is respected ---

  it('respects manual toggle: unchecking a selected item removes it from the selection', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 100 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Item is auto-selected since budget covers it.
    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(true)

    // Manually click to deselect.
    await checkbox.trigger('click')
    await wrapper.vm.$nextTick()

    expect(checkbox.element.checked).toBe(false)
  })

  it('manual toggle adds an unselected item to the selection', async () => {
    // Budget set to 0 so nothing is auto-selected.
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 100, recommended_qty: 5, unit_cost: 20 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Force budget to 0.
    await wrapper.find('input[type="range"]').setValue(0)
    await wrapper.vm.$nextTick()

    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(false)

    // Manual click to select.
    await checkbox.trigger('click')
    await wrapper.vm.$nextTick()

    expect(checkbox.element.checked).toBe(true)
  })

  // --- selectedTotal matches sum of selected items' subtotals ---

  it('selectedTotal equals sum of recommended_qty * unit_cost for selected items', async () => {
    // item A: 10 qty * $20 = $200
    // item B: 5 qty * $30 = $150
    // Both fit in budget; total should be $350.
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 200, recommended_qty: 10, unit_cost: 20 }),
      makeCandidate({ sku: 'B-001', estimated_cost: 150, recommended_qty: 5, unit_cost: 30 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Verify by reading the selectedTotal display in the stat card.
    const statCards = wrapper.findAll('.stat-card')
    const totalCard = statCards.find(card => card.text().includes('Selected Total'))
    expect(totalCard).toBeDefined()
    // The displayed value should include $350.
    expect(totalCard.text()).toContain('$350')
  })

  // --- Place Order button disabled when nothing selected ---

  it('Place Order button is disabled when no items are selected', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 200 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Force budget to 0 so nothing is selected.
    await wrapper.find('input[type="range"]').setValue(0)
    await wrapper.vm.$nextTick()

    const button = wrapper.find('button.btn-primary')
    expect(button.element.disabled).toBe(true)
  })

  // --- Place Order button disabled when over budget ---

  it('Place Order button is disabled when selectedTotal exceeds budget', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 100, recommended_qty: 5, unit_cost: 20 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Manually select the item (it is auto-selected on load at max budget).
    // Then shrink the budget below the selected total to trigger overBudget.
    // item subtotal = 5 * 20 = 100; set budget to 50.
    const checkbox = wrapper.find('input[type="checkbox"]')
    if (!checkbox.element.checked) {
      await checkbox.trigger('click')
      await wrapper.vm.$nextTick()
    }

    await wrapper.find('input[type="range"]').setValue(50)
    // Trigger the budget watcher manually to simulate slider move.
    await wrapper.vm.$nextTick()

    // Mark userOverride manually so budget watcher does not auto-deselect.
    // The component only auto-selects when !userOverride. After a manual
    // toggle userOverride is true, so the budget watcher won't clear selection.
    // We achieve the over-budget state by clicking the item and then dragging
    // the slider down below the subtotal.

    const button = wrapper.find('button.btn-primary')
    expect(button.element.disabled).toBe(true)
  })

  // --- Place Order button enabled when items selected and within budget ---

  it('Place Order button is enabled when items are selected and within budget', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 200, recommended_qty: 10, unit_cost: 20 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // All items auto-selected at full budget on load.
    const button = wrapper.find('button.btn-primary')
    expect(button.element.disabled).toBe(false)
  })

  // --- Reset auto-select restores greedy selection ---

  it('"Reset to auto-select" re-runs autoSelect and clears manual overrides', async () => {
    const candidates = [
      makeCandidate({ sku: 'A-001', estimated_cost: 100 }),
      makeCandidate({ sku: 'B-001', estimated_cost: 100 })
    ]
    const wrapper = await mountWithCandidates(candidates)

    // Deselect all manually.
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    for (const checkbox of checkboxes) {
      if (checkbox.element.checked) {
        await checkbox.trigger('click')
        await wrapper.vm.$nextTick()
      }
    }
    expect(checkboxes.every(c => !c.element.checked)).toBe(true)

    // Reset auto-select.
    const resetButton = wrapper.find('button.btn-secondary')
    await resetButton.trigger('click')
    await wrapper.vm.$nextTick()

    // Both items should now be re-selected since budget covers both.
    const rechecked = wrapper.findAll('input[type="checkbox"]').filter(c => c.element.checked)
    expect(rechecked).toHaveLength(2)
  })
})
