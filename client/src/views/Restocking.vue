<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget slider -->
      <div class="card budget-card">
        <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
        <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        <input
          type="range"
          class="budget-slider"
          :min="MIN_BUDGET"
          :max="MAX_BUDGET"
          :step="BUDGET_STEP"
          v-model.number="budget"
          :style="sliderStyle"
          :aria-label="t('restocking.budgetLabel')"
          :aria-valuetext="formatCurrency(budget, currentCurrency)"
        />
        <div class="budget-range-labels">
          <span>{{ formatCurrency(MIN_BUDGET, currentCurrency) }}</span>
          <span>{{ formatCurrency(MAX_BUDGET, currentCurrency) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ formatCurrency(recommendation.totalCost, currentCurrency) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(recommendation.remaining, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendation.recommended.length }}</div>
        </div>
      </div>

      <!-- Recommended basket -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
            <p class="card-subtitle">{{ t('restocking.recommendedCount', { count: recommendation.recommended.length }) }}</p>
          </div>
        </div>

        <div v-if="recommendation.recommended.length > 0" class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.priority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation.recommended" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td class="on-hand-cell">
                  <span class="on-hand-value">{{ item.quantity_on_hand }}</span>
                  <span class="on-hand-divider">/</span>
                  <span class="on-hand-value">{{ item.reorder_point }}</span>
                  <div class="on-hand-caption">{{ t('restocking.table.reorderPoint') }}</div>
                </td>
                <td>{{ item.quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td><strong>{{ formatCurrency(item.lineCost, currentCurrency) }}</strong></td>
                <td>{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
                <td>
                  <span :class="['badge', item.priority]">{{ t(`priority.${item.priority}`) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">
          {{ recommendation.skipped.length > 0 ? t('restocking.budgetTooLow') : t('restocking.noRecommendations') }}
        </div>
      </div>

      <!-- Items that didn't fit the remaining budget -->
      <div v-if="recommendation.skipped.length > 0" class="card skipped-card">
        <div class="card-header">
          <div>
            <h3 class="card-title">{{ t('restocking.skipped') }}</h3>
            <p class="card-subtitle">{{ t('restocking.skippedCount', { count: recommendation.skipped.length }) }}</p>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation.skipped" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ formatCurrency(item.lineCost, currentCurrency) }}</td>
                <td class="over-budget">{{ t('restocking.overBudgetBy', { amount: formatCurrency(item.overBudgetBy, currentCurrency) }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Submission -->
      <div class="place-order-area">
        <div v-if="submitError" class="error submit-error">{{ submitError }}</div>
        <div v-if="lastSubmittedOrder" class="success-panel">
          <p>{{ t('restocking.orderPlaced', { orderNumber: lastSubmittedOrder.order_number }) }}</p>
          <router-link to="/orders" class="view-link">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
        <button
          type="button"
          class="po-button create place-order-button"
          :disabled="submitting || recommendation.recommended.length === 0"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import { useRestocking, buildRecommendation, MIN_BUDGET, MAX_BUDGET, BUDGET_STEP } from '../composables/useRestocking'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const submitError = ref(null)
    const inventoryItems = ref([])
    const forecasts = ref([])

    // Inventory has no time dimension, so only warehouse/category filters apply here
    // (matches Inventory.vue and Demand.vue - month is intentionally not watched).
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const { budget, submitting, lastSubmittedOrder, submitOrder, clearLastSubmittedOrder } = useRestocking()

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const [inventoryData, forecastData] = await Promise.all([
          api.getInventory({ warehouse: filters.warehouse, category: filters.category }),
          api.getDemandForecasts()
        ])
        inventoryItems.value = inventoryData
        forecasts.value = forecastData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    // The basket is derived with a computed property rather than fetched from the
    // server: inventory/forecast data only changes on filter changes (handled above),
    // while the budget changes continuously as the user drags the slider. Recomputing
    // client-side keeps the slider instantaneous with no network round-trip per step.
    const recommendation = computed(() => buildRecommendation(inventoryItems.value, forecasts.value, budget.value))

    // Percentage of the slider track that represents the current budget, used to
    // paint the "filled" portion of the track. Guarded against a zero-width range.
    const budgetPercent = computed(() => {
      const range = MAX_BUDGET - MIN_BUDGET
      if (range <= 0) return 0
      return ((budget.value - MIN_BUDGET) / range) * 100
    })

    // Native range inputs don't expose a cross-browser "filled track" pseudo-element,
    // so the fill is faked with a two-stop linear-gradient background on the input
    // itself, split at the current budget percentage.
    const sliderStyle = computed(() => ({
      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${budgetPercent.value}%, #e2e8f0 ${budgetPercent.value}%, #e2e8f0 100%)`
    }))

    // A stale success/error banner shouldn't linger once the basket underneath it
    // has changed, so clear both whenever the budget or filters move.
    watch([budget, selectedLocation, selectedCategory], () => {
      clearLastSubmittedOrder()
      submitError.value = null
    })

    const placeOrder = async () => {
      submitError.value = null
      try {
        await submitOrder(api, recommendation.value.recommended, budget.value)
      } catch (err) {
        // A failed submit must not wipe the recommendation - only surface the error.
        submitError.value = 'Failed to submit restock order: ' + err.message
        console.error(err)
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      submitError,
      recommendation,
      budget,
      submitting,
      lastSubmittedOrder,
      placeOrder,
      sliderStyle,
      MIN_BUDGET,
      MAX_BUDGET,
      BUDGET_STEP,
      currentCurrency,
      formatCurrency,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-subtitle {
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
}

/* Budget card */
.budget-card {
  padding: 1.5rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}

.budget-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

/* Range slider - first native range input in this codebase, so it needs full
   cross-browser styling (no shared convention to reuse). */
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-runnable-track {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: transparent;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  margin-top: -6px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: background 0.15s ease;
}

.budget-slider:hover::-webkit-slider-thumb,
.budget-slider:active::-webkit-slider-thumb {
  background: #2563eb;
}

.budget-slider::-moz-range-track {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: transparent;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: background 0.15s ease;
}

.budget-slider:hover::-moz-range-thumb,
.budget-slider:active::-moz-range-thumb {
  background: #2563eb;
}

.budget-slider:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  border-radius: 4px;
}

.budget-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider:focus::-moz-range-thumb {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), 0 1px 3px rgba(0, 0, 0, 0.3);
}

/* On-hand / reorder point cell */
.on-hand-cell {
  white-space: nowrap;
}

.on-hand-value {
  font-weight: 600;
  color: #0f172a;
}

.on-hand-divider {
  color: #94a3b8;
  margin: 0 0.25rem;
}

.on-hand-caption {
  font-size: 0.688rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-top: 0.125rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Skipped items are muted - they're informational, not actionable */
.skipped-card {
  opacity: 0.75;
}

.skipped-card:hover {
  opacity: 1;
}

.over-budget {
  color: #ea580c;
  font-weight: 600;
  font-size: 0.813rem;
  white-space: nowrap;
}

/* Place order area */
.place-order-area {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
}

/* Scoped styles don't leak across components, so the .po-button/.po-button.create
   shape (Dashboard.vue, ~lines 1239-1259) is reproduced here rather than reused. */
.po-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.po-button.create {
  background: #3b82f6;
  color: white;
}

.po-button.create:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.place-order-button {
  padding: 0.75rem 1.75rem;
  font-size: 0.938rem;
}

.place-order-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-error {
  width: 100%;
  text-align: left;
}

.success-panel {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
}

.success-panel p {
  margin: 0;
}

.view-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.view-link:hover {
  color: #047857;
}
</style>
