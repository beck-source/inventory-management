import { ref } from 'vue'

// Shared restocking state (singleton pattern) - keeps the budget slider
// position when the user navigates away from the Restocking tab and back.
const budget = ref(50000)
const submitting = ref(false)
const lastSubmittedOrder = ref(null)

export const MIN_BUDGET = 5000
export const MAX_BUDGET = 250000
export const BUDGET_STEP = 5000

// The inventory data has no target/max stock level, so the restock target is
// derived: 1.5x the reorder point. That matches the "adequate" stock band
// already used by Inventory.vue, so restocking lifts an item just clear of the
// low-stock threshold rather than to an arbitrary number.
const RESTOCK_TARGET_MULTIPLIER = 1.5

// Urgency weights are tuning constants chosen for demo readability, not values
// derived from the data. Stock shortfall dominates; rising demand breaks ties.
const SHORTFALL_WEIGHT = 100
const DEMAND_GROWTH_WEIGHT = 50
const INCREASING_TREND_BONUS = 10

/**
 * Score how badly an item needs restocking. Higher is more urgent.
 * `forecast` is optional - most inventory SKUs have no demand forecast.
 */
function scoreUrgency(item, forecast) {
  const target = item.reorder_point * RESTOCK_TARGET_MULTIPLIER
  const shortfall = Math.max(0, target - item.quantity_on_hand)

  // Guard against a zero reorder_point producing a divide-by-zero.
  const shortfallRatio = target > 0 ? shortfall / target : 0

  let demandGrowth = 0
  if (forecast && forecast.current_demand > 0) {
    demandGrowth = (forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand
  }

  const trendBonus = forecast && forecast.trend === 'increasing' ? INCREASING_TREND_BONUS : 0

  return {
    shortfall: Math.ceil(shortfall),
    urgency: shortfallRatio * SHORTFALL_WEIGHT + demandGrowth * DEMAND_GROWTH_WEIGHT + trendBonus,
    demandGrowth
  }
}

function priorityFromUrgency(urgency) {
  if (urgency >= 60) return 'high'
  if (urgency >= 30) return 'medium'
  return 'low'
}

/**
 * Build a restock basket that fits within `budget`, greedy by urgency.
 *
 * Pure function (no reactive state) so it can be unit tested and so the view
 * can call it from a computed property.
 *
 * Returns { recommended, skipped, totalCost, remaining }. Items that don't fit
 * the remaining budget are pushed to `skipped` and the walk *continues* to the
 * next candidate rather than stopping, so a single expensive item can't strand
 * the rest of the budget.
 */
export function buildRecommendation(inventoryItems, forecasts, budget) {
  const forecastsBySku = new Map((forecasts || []).map(f => [f.item_sku, f]))

  const candidates = (inventoryItems || [])
    .map(item => {
      const forecast = forecastsBySku.get(item.sku)
      const { shortfall, urgency, demandGrowth } = scoreUrgency(item, forecast)
      return {
        sku: item.sku,
        name: item.name,
        category: item.category,
        warehouse: item.warehouse,
        quantity_on_hand: item.quantity_on_hand,
        reorder_point: item.reorder_point,
        unit_cost: item.unit_cost,
        lead_time_days: item.lead_time_days,
        quantity: shortfall,
        lineCost: Math.round(shortfall * item.unit_cost * 100) / 100,
        urgency,
        demandGrowth,
        hasForecast: Boolean(forecast),
        priority: priorityFromUrgency(urgency)
      }
    })
    // Only items actually below the restock target are candidates.
    .filter(candidate => candidate.quantity > 0)
    .sort((a, b) => b.urgency - a.urgency)

  const recommended = []
  const skipped = []
  let remaining = budget

  for (const candidate of candidates) {
    if (candidate.lineCost <= remaining) {
      recommended.push(candidate)
      remaining = Math.round((remaining - candidate.lineCost) * 100) / 100
    } else {
      skipped.push({ ...candidate, overBudgetBy: Math.round((candidate.lineCost - remaining) * 100) / 100 })
    }
  }

  const totalCost = Math.round(recommended.reduce((sum, item) => sum + item.lineCost, 0) * 100) / 100

  return { recommended, skipped, totalCost, remaining }
}

export function useRestocking() {
  // Trim each line to the fields the API expects - the recommendation carries
  // extra display-only fields the backend model would reject.
  const submitOrder = async (api, recommended, budgetValue) => {
    const payload = {
      budget: budgetValue,
      items: recommended.map(item => ({
        sku: item.sku,
        name: item.name,
        quantity: item.quantity,
        unit_cost: item.unit_cost,
        lead_time_days: item.lead_time_days
      }))
    }

    submitting.value = true
    try {
      const order = await api.createRestockOrder(payload)
      lastSubmittedOrder.value = order
      return order
    } finally {
      submitting.value = false
    }
  }

  const clearLastSubmittedOrder = () => {
    lastSubmittedOrder.value = null
  }

  return {
    // State
    budget,
    submitting,
    lastSubmittedOrder,

    // Methods
    submitOrder,
    clearLastSubmittedOrder
  }
}
