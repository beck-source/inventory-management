<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget card stays mounted at all times (no page-level v-if/v-else) so the
         slider never unmounts mid-drag while recommendations refetch in the background. -->
    <div class="card">
      <div class="card-title">{{ t('restocking.budgetLabel') }}</div>
      <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      <!--
        v-model.number is required here: without the .number modifier, budget becomes a
        string ("65000") from the range input's value, which silently breaks
        .toLocaleString() formatting and any arithmetic (string concatenation instead
        of addition) further down.
      -->
      <input
        type="range"
        class="budget-slider"
        :min="budgetMin"
        :max="budgetMax"
        :step="budgetStep"
        v-model.number="budget"
      />
      <div class="budget-scale">
        <span>{{ currencySymbol }}{{ budgetMin.toLocaleString() }}</span>
        <span>{{ currencySymbol }}{{ budgetMax.toLocaleString() }}</span>
      </div>
    </div>

    <div class="stats-grid">
      <!-- No "Budget" tile here: the chosen budget is already the large readout directly
           above, and a fourth tile wrapped onto its own row leaving the grid half empty. -->
      <div class="stat-card success">
        <div class="stat-label">{{ t('restocking.allocated') }}</div>
        <div class="stat-value">{{ currencySymbol }}{{ formatMoney(totalCost) }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">{{ t('restocking.remaining') }}</div>
        <div class="stat-value">{{ currencySymbol }}{{ formatMoney(remainingBudget) }}</div>
      </div>
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
        <div class="stat-value">{{ recommendations.length }}</div>
      </div>
    </div>

    <div v-if="placedOrder" class="order-success-banner">
      {{ t('restocking.orderPlacedDetail', { orderNumber: placedOrder.order_number, days: placedOrder.lead_time_days }) }}
      <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        <button
          class="place-order-btn"
          :disabled="loading || submitting || recommendations.length === 0"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="candidateCount === 0" class="loading">{{ t('restocking.noCandidates') }}</div>
      <div v-else-if="recommendations.length === 0" class="loading">
        {{ t('restocking.budgetTooLow', { amount: currencySymbol + (minUnitCost !== null ? formatMoney(minUnitCost) : '') }) }}
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.category') }}</th>
              <th>{{ t('restocking.table.warehouse') }}</th>
              <th>{{ t('restocking.table.onHand') }}</th>
              <th>{{ t('restocking.table.reorderPoint') }}</th>
              <th>{{ t('restocking.table.shortfall') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.lineCost') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations" :key="item.sku">
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ translateProductName(item.name) }}</td>
              <td>{{ item.category }}</td>
              <td>{{ translateWarehouse(item.warehouse) }}</td>
              <td class="numeric">
                {{ item.quantity_on_hand }}
                <span v-if="item.below_reorder_point" class="badge danger">{{ t('status.lowStock') }}</span>
              </td>
              <td class="numeric">{{ item.reorder_point }}</td>
              <td class="numeric">{{ item.shortfall }}</td>
              <td>
                <span v-if="item.forecast_trend" :class="['badge', item.forecast_trend]">
                  {{ t('trends.' + item.forecast_trend) }}
                </span>
                <span v-else>&mdash;</span>
              </td>
              <td class="numeric">{{ currencySymbol }}{{ formatMoney(item.unit_cost) }}</td>
              <td class="numeric">
                {{ item.recommended_quantity }}
                <span v-if="!item.fully_covered" class="badge warning">{{ t('restocking.partial') }}</span>
              </td>
              <td class="numeric">{{ currencySymbol }}{{ formatMoney(item.line_cost) }}</td>
              <td>{{ item.lead_time_days }} {{ t('restocking.daysUnit') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Money always carries two decimals. Plain toLocaleString() renders 89.5 as "$89.5",
    // which reads as a broken price rather than $89.50. The budget readout and slider
    // scale stay whole: the step is 1000, so they can never land on a fraction.
    const formatMoney = (value) => {
      return (value || 0).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    // Watch only warehouse/category from shared filters. Time period and order status
    // don't apply: restocking recommendations have no time dimension, and order status
    // describes orders that have already been placed, not ones being planned.
    const { selectedLocation, selectedCategory } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    const recommendations = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const candidateCount = ref(0)
    const minUnitCost = ref(null)

    const budgetMin = 0
    const budgetStep = ref(1000)
    const budgetMax = ref(1000)
    const budget = ref(0)

    let boundsInitialized = false
    let debounceTimer = null
    let requestId = 0

    const deriveBounds = async () => {
      // Probe with budget=0 to learn max_useful_cost for the current filters, without
      // spending the user's current budget selection.
      const filters = { warehouse: selectedLocation.value, category: selectedCategory.value }
      try {
        const probe = await api.getRestockRecommendations(0, filters)
        const maxUseful = probe.max_useful_cost || 0
        budgetMax.value = Math.max(1000, Math.ceil(maxUseful / 1000) * 1000)
        budgetStep.value = 1000

        if (!boundsInitialized) {
          budget.value = Math.round((budgetMax.value / 2) / budgetStep.value) * budgetStep.value
          boundsInitialized = true
        } else {
          // Keep the user's chosen budget on filter change, just clamp to new bounds.
          budget.value = Math.min(budget.value, budgetMax.value)
        }
      } catch (err) {
        // If the probe fails, fall back to a safe default and let fetchRecommendations
        // surface the real error.
        console.error('Failed to derive restocking bounds:', err)
      }
    }

    const fetchRecommendations = async () => {
      const myId = ++requestId
      loading.value = true
      error.value = null
      try {
        const filters = { warehouse: selectedLocation.value, category: selectedCategory.value }
        const data = await api.getRestockRecommendations(budget.value, filters)

        // Discard stale responses: a slow early request (e.g. for a budget the user has
        // already dragged past) can resolve after a faster later one.
        if (myId !== requestId) return

        recommendations.value = data.items || []
        totalCost.value = data.total_cost || 0
        remainingBudget.value = data.remaining_budget || 0
        candidateCount.value = data.candidate_count || 0
        minUnitCost.value = data.min_unit_cost
      } catch (err) {
        if (myId !== requestId) return
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        if (myId === requestId) loading.value = false
      }
    }

    const loadForFilters = async () => {
      await deriveBounds()
      await fetchRecommendations()
    }

    // Debounce ordinary slider drags by 250ms (no lodash/@vueuse available in this
    // project) so we don't fire a request per pixel of thumb movement.
    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        fetchRecommendations()
      }, 250)
    })

    // Filter changes re-derive the budget bounds (and clamp/re-fetch); a plain slider
    // move never touches this watcher, so it can't fight the user's thumb.
    watch([selectedLocation, selectedCategory], () => {
      loadForFilters()
    })

    onMounted(loadForFilters)

    onUnmounted(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
    })

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const orderData = {
          budget: budget.value,
          items: recommendations.value.map(item => ({
            sku: item.sku,
            quantity: item.recommended_quantity
          }))
        }
        placedOrder.value = await api.createRestockOrder(orderData)
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    return {
      t,
      currencySymbol,
      formatMoney,
      translateProductName,
      translateWarehouse,
      loading,
      error,
      submitting,
      submitError,
      placedOrder,
      recommendations,
      totalCost,
      remainingBudget,
      candidateCount,
      minUnitCost,
      budgetMin,
      budgetMax,
      budgetStep,
      budget,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-readout {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin: 0.5rem 0 1rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  -webkit-appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.35);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (prefers-reduced-motion: reduce) {
  .place-order-btn:hover:not(:disabled) {
    transform: none;
  }
}

.order-success-banner {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.order-success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}

.numeric {
  font-variant-numeric: tabular-nums;
}
</style>
