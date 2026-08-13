<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.availableBudget') }}</h3>
        </div>
        <div class="budget-value">{{ formatCurrency(budgetInput, currentCurrency) }}</div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          step="500"
          v-model.number="budgetInput"
          :disabled="data && data.candidate_count === 0"
        />
        <div class="budget-range-labels">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(sliderMax, currentCurrency) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.availableBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(data ? data.budget : budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetUsed') }}</div>
          <div class="stat-value">{{ formatCurrency(data ? data.budget_used : 0, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrency(data ? data.budget_remaining : 0, currentCurrency) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <!-- Lines actually being ordered, not candidate_count: the budget usually
               covers only some of the items that are short. -->
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <!-- Three distinct empty states: nothing needs restocking, budget too low to afford anything, or a real table -->
      <div v-if="data && data.candidate_count === 0" class="card">
        <div class="empty-state">{{ t('restocking.allStocked') }}</div>
      </div>
      <div v-else-if="data && data.candidate_count > 0 && recommendations.length === 0" class="card">
        <div class="empty-state">
          {{ t('restocking.budgetTooLow', { amount: formatCurrencyWithDecimals(data.cheapest_unit_cost, currentCurrency, 2) }) }}
        </div>
      </div>
      <div v-else class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.itemName') }}</th>
                <th>{{ t('orders.table.category') }}</th>
                <th>{{ t('orders.table.warehouse') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.reorderPoint') }}</th>
                <th>{{ t('restocking.table.target') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.orderQuantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.priority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.reorder_point }}</td>
                <td>{{ item.target_quantity }}</td>
                <td>{{ item.shortfall }}</td>
                <td>
                  <strong>{{ item.recommended_quantity }}</strong>
                  <span v-if="!item.fully_covered" class="badge info partial-badge">{{ t('restocking.partial') }}</span>
                </td>
                <td>{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td><strong>{{ formatCurrency(item.line_cost, currentCurrency) }}</strong></td>
                <td>{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
                <td>
                  <span :class="['badge', item.priority === 'critical' ? 'danger' : 'warning']">
                    {{ item.priority === 'critical' ? t('restocking.critical') : t('restocking.low') }}
                  </span>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="10"><strong>{{ t('restocking.budgetUsed') }}</strong></td>
                <td><strong>{{ formatCurrency(data.budget_used, currentCurrency) }}</strong></td>
                <td colspan="2"></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="place-order-row">
          <button
            class="place-order-btn"
            :disabled="submitting || recommendations.length === 0 || !!submittedOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <!-- Submission failure must stay local to this card - it must never blank the whole page via the page-level error ref -->
        <div v-if="submitError" class="error">{{ submitError }}</div>

        <div v-if="submittedOrder" class="success-banner">
          <p>{{ t('restocking.orderPlaced', { orderNumber: submittedOrder.order_number }) }}</p>
          <p>
            {{ t('restocking.orderPlacedDetail', {
              date: formatDeliveryDate(submittedOrder.expected_delivery),
              days: submittedOrder.lead_time_days
            }) }}
          </p>
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useFilters } from '../composables/useFilters'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName, translateWarehouse } = useI18n()

    // The global FilterBar is rendered above every view, so honour the two filters the
    // recommendations endpoint understands rather than leaving visible controls inert.
    // Period and status are skipped deliberately: inventory has no time dimension and
    // no order status, which is the same reason /api/inventory ignores them.
    const { selectedLocation, selectedCategory } = useFilters()

    // budgetInput drives the slider UI directly (instant visual feedback);
    // budget is the debounced mirror that actually triggers a fetch.
    const budgetInput = ref(20000)
    const budget = ref(20000)

    const data = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submittedOrder = ref(null)
    const submitError = ref(null)

    const recommendations = computed(() => data.value ? data.value.recommendations : [])

    // Slider top means "enough budget to buy everything currently short" - derived from the
    // last response's total_shortfall_cost so a fully-stocked warehouse doesn't get a dead max=0 slider.
    const sliderMax = computed(() => {
      const shortfall = data.value ? data.value.total_shortfall_cost : 60000
      return Math.max(5000, Math.ceil((shortfall || 60000) / 5000) * 5000)
    })

    let debounceTimer = null
    watch(budgetInput, (val) => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        budget.value = val
      }, 200)
    })

    // Request counter guards against out-of-order responses: rapid debounced budget drags
    // can still fire overlapping requests, and a slow earlier response must never clobber a newer one.
    let requestCounter = 0

    const loadRecommendations = async () => {
      const requestId = ++requestCounter
      loading.value = true
      error.value = null
      try {
        const response = await api.getRestockRecommendations(budget.value, {
          warehouse: selectedLocation.value,
          category: selectedCategory.value
        })
        if (requestId !== requestCounter) return
        data.value = response
      } catch (err) {
        if (requestId !== requestCounter) return
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        if (requestId === requestCounter) {
          loading.value = false
        }
      }
    }

    watch([budget, selectedLocation, selectedCategory], () => {
      // Re-arm the place-order button whenever the budget or filters change so the user
      // can't accidentally resubmit the order they just placed against a different basket.
      submittedOrder.value = null
      submitError.value = null
      loadRecommendations()
    })

    // Category names live in the data in English; useI18n only ships helpers for
    // product and warehouse names, so map them here as Inventory.vue does.
    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const formatDeliveryDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({ sku: r.sku, quantity: r.recommended_quantity }))
        })
        submittedOrder.value = order
      } catch (err) {
        // Submission failures stay local - never touch the page-level error ref
        submitError.value = t('restocking.orderFailed') + ': ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currentCurrency,
      budgetInput,
      budget,
      data,
      loading,
      error,
      submitting,
      submittedOrder,
      submitError,
      recommendations,
      sliderMax,
      placeOrder,
      formatDeliveryDate,
      formatCurrency,
      formatCurrencyWithDecimals,
      translateProductName,
      translateWarehouse,
      translateCategory
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
  font-size: 0.938rem;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 1rem;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  cursor: pointer;
  margin-bottom: 0.5rem;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
}

.budget-slider:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.budget-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.partial-badge {
  margin-left: 0.5rem;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}

.success-banner p {
  margin-bottom: 0.375rem;
}

.success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}
</style>
