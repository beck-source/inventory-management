<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set an available budget and review the recommended restocking order.</p>
    </div>

    <div v-if="loading" class="loading">Loading restocking recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-control">
          <input
            v-model.number="budget"
            type="range"
            class="budget-slider"
            :min="BUDGET_MIN"
            :max="BUDGET_MAX"
            :step="BUDGET_STEP"
          />
          <div class="budget-readout">{{ formatMoney(budget) }}</div>
        </div>
        <div class="budget-bounds">
          <span>{{ formatMoney(BUDGET_MIN) }}</span>
          <span>{{ formatMoney(BUDGET_MAX) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Items Recommended</div>
          <div class="stat-value">{{ allocation.affordable.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Order Total</div>
          <div class="stat-value">{{ formatMoney(allocation.spent) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Budget Remaining</div>
          <div class="stat-value">{{ formatMoney(budget - allocation.spent) }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">Not Funded</div>
          <div class="stat-value">{{ allocation.skipped.length }}</div>
        </div>
      </div>

      <div v-if="successMessage" class="notice notice-success">{{ successMessage }}</div>
      <div v-if="submitError" class="notice notice-error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Order ({{ allocation.affordable.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="allocation.affordable.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Submitting...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="candidates.length === 0" class="empty-state">
          No items currently need restocking for the selected filters.
        </div>
        <div v-else-if="allocation.affordable.length === 0" class="empty-state">
          Budget is too low to fund any item. The cheapest candidate costs
          {{ formatMoney(cheapestCandidateCost) }}.
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item</th>
                <th>Category</th>
                <th>Warehouse</th>
                <th class="num">On Hand</th>
                <th class="num">Reorder Pt</th>
                <th class="num">Qty to Order</th>
                <th class="num">Unit Cost</th>
                <th class="num">Est. Cost</th>
                <th>Priority</th>
                <th>Demand Signal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in allocation.affordable" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.warehouse }}</td>
                <td class="num">{{ item.quantity_on_hand }}</td>
                <td class="num">{{ item.reorder_point }}</td>
                <td class="num"><strong>{{ item.recommended_quantity }}</strong></td>
                <td class="num">{{ formatMoney(item.unit_cost) }}</td>
                <td class="num"><strong>{{ formatMoney(item.estimated_cost) }}</strong></td>
                <td>
                  <span :class="['badge', priorityClass(item.priority)]">{{ item.priority }}</span>
                </td>
                <td>
                  <span v-if="item.demand_trend">
                    {{ item.demand_trend }} ({{ item.forecasted_demand }})
                  </span>
                  <span v-else class="muted">&mdash;</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="allocation.skipped.length > 0" class="card">
        <div class="card-header">
          <h3 class="card-title">Not Funded By This Budget ({{ allocation.skipped.length }})</h3>
        </div>
        <div class="table-container">
          <table class="restock-table skipped">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item</th>
                <th>Warehouse</th>
                <th class="num">Qty Needed</th>
                <th class="num">Est. Cost</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in allocation.skipped" :key="item.sku">
                <td>{{ item.sku }}</td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ item.warehouse }}</td>
                <td class="num">{{ item.recommended_quantity }}</td>
                <td class="num">{{ formatMoney(item.estimated_cost) }}</td>
                <td>
                  <span :class="['badge', priorityClass(item.priority)]">{{ item.priority }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
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

const BUDGET_MIN = 0
const BUDGET_MAX = 50000
const BUDGET_STEP = 500

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    const candidates = ref([])
    const budget = ref(25000)

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const formatMoney = (amount) => formatCurrency(amount, currentCurrency.value)

    // Greedy fill: candidates arrive from the API already ordered urgent-then-cheapest,
    // so walking them in order spends the budget on the most critical shortfalls first.
    // Kept as a computed so dragging the slider never re-hits the API.
    const allocation = computed(() => {
      const affordable = []
      const skipped = []
      let spent = 0

      for (const item of candidates.value) {
        if (spent + item.estimated_cost <= budget.value) {
          affordable.push(item)
          // Re-round each step to stop float drift accumulating across many items.
          spent = Math.round((spent + item.estimated_cost) * 100) / 100
        } else {
          skipped.push(item)
        }
      }

      return { affordable, skipped, spent }
    })

    const cheapestCandidateCost = computed(() => {
      if (candidates.value.length === 0) return 0
      return Math.min(...candidates.value.map(item => item.estimated_cost))
    })

    const priorityClass = (priority) => {
      const priorityMap = {
        high: 'danger',
        medium: 'warning',
        low: 'info'
      }
      return priorityMap[priority] || 'info'
    }

    const loadCandidates = async () => {
      try {
        loading.value = true
        error.value = null
        candidates.value = await api.getRestockCandidates(getCurrentFilters())
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      successMessage.value = null

      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: allocation.value.affordable.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost
          }))
        })

        successMessage.value =
          `Order ${order.order_number} submitted - ${order.item_count} items, ` +
          `${formatMoney(order.total_cost)}, arriving in ${order.lead_time_days} days. ` +
          `View it under Submitted Orders on the Orders tab.`

        await loadCandidates()
      } catch (err) {
        submitError.value = err.response?.data?.detail || ('Failed to place order: ' + err.message)
      } finally {
        submitting.value = false
      }
    }

    // Warehouse and category are the only filters the candidates endpoint accepts.
    watch([selectedLocation, selectedCategory], loadCandidates)

    onMounted(loadCandidates)

    return {
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      loading,
      error,
      submitting,
      submitError,
      successMessage,
      candidates,
      budget,
      allocation,
      cheapestCandidateCost,
      priorityClass,
      placeOrder,
      formatMoney,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid #ffffff;
  cursor: pointer;
}

.budget-readout {
  min-width: 140px;
  text-align: right;
  font-size: 1.5rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.restock-table {
  width: 100%;
}

.restock-table .num {
  text-align: right;
}

.restock-table.skipped {
  opacity: 0.6;
}

.muted {
  color: #64748b;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.notice {
  padding: 0.875rem 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.notice-success {
  background: #f0fdf4;
  border: 1px solid #86efac;
  color: #166534;
}

.notice-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}
</style>
