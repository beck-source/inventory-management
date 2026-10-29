import { computed } from 'vue'

const BUDGET_STEP = 1000

// Work in whole cents so float noise in unit_cost * quantity cannot flip a budget comparison.
const getItemCostCents = (forecast) => Math.round(forecast.forecasted_demand * forecast.unit_cost * 100)

const getGrowth = (forecast) => {
  if (forecast.current_demand <= 0) return forecast.forecasted_demand > 0 ? Infinity : 0
  return (forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand
}

const isRestockCandidate = (forecast) => forecast.trend !== 'decreasing'

/**
 * Returns the smallest multiple of the slider step that covers the cost of every
 * non-decreasing item, so the slider maximum is always reachable.
 */
export function getMaxBudget(forecasts) {
  const totalCents = forecasts
    .filter(isRestockCandidate)
    .reduce((sum, forecast) => sum + getItemCostCents(forecast), 0)
  return Math.ceil(totalCents / 100 / BUDGET_STEP) * BUDGET_STEP
}

/** Returns half of the max budget rounded to the nearest slider step. */
export function getDefaultBudget(maxBudget) {
  return Math.round(maxBudget / 2 / BUDGET_STEP) * BUDGET_STEP
}

/**
 * Picks whole items for a budget: ranks non-decreasing forecasts by growth (highest first,
 * ties keep original order), then adds each item that still fits and skips the rest.
 * Each result is { sku, name, trend, quantity, unitCost, lineCost, leadTimeDays }.
 */
export function getRecommendations(forecasts, budget) {
  const ranked = forecasts
    .filter(isRestockCandidate)
    .map(forecast => ({ forecast, growth: getGrowth(forecast) }))
    .sort((a, b) => (b.growth > a.growth ? 1 : b.growth < a.growth ? -1 : 0))

  let remainingCents = Math.round(budget * 100)
  const picked = []

  for (const { forecast } of ranked) {
    const costCents = getItemCostCents(forecast)
    if (costCents > remainingCents) continue
    remainingCents -= costCents
    picked.push({
      sku: forecast.item_sku,
      name: forecast.item_name,
      trend: forecast.trend,
      quantity: forecast.forecasted_demand,
      unitCost: forecast.unit_cost,
      lineCost: costCents / 100,
      leadTimeDays: forecast.lead_time_days
    })
  }

  return picked
}

/** Reactive wrapper: forecasts and budget are refs. */
export function useRestockingRecommendations(forecasts, budget) {
  const maxBudget = computed(() => getMaxBudget(forecasts.value))
  const recommendations = computed(() => getRecommendations(forecasts.value, budget.value))

  return { maxBudget, recommendations }
}
