<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Allocate your restocking budget to the items with the highest demand gaps.</p>
    </div>

    <!-- Success Banner -->
    <div v-if="successMessage" class="success-banner">
      {{ successMessage }}
    </div>

    <!-- Error Banner -->
    <div v-if="submitError" class="error">
      {{ submitError }}
    </div>

    <!-- Budget Slider Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Budget Allocation</h3>
      </div>
      <div class="slider-section">
        <div class="budget-display">{{ formattedBudget }}</div>
        <input
          type="range"
          class="budget-slider"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          v-model.number="budget"
        />
        <div class="slider-labels">
          <span>{{ formatCurrency(BUDGET_MIN) }}</span>
          <span>{{ formatCurrency(BUDGET_MAX) }}</span>
        </div>
      </div>
    </div>

    <!-- Recommendations Table Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Restocking Recommendations</h3>
        <span class="item-count">{{ recommendations.length }} item{{ recommendations.length !== 1 ? 's' : '' }}</span>
      </div>

      <div v-if="loading" class="loading">Loading demand forecasts...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        No restocking recommendations within this budget. Try increasing the budget or there may be no demand gaps.
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Item Name</th>
              <th>Trend</th>
              <th>Demand Gap</th>
              <th>Qty to Order</th>
              <th>Unit Cost</th>
              <th>Subtotal</th>
              <th>Lead Time</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations" :key="item.sku">
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ item.name }}</td>
              <td>
                <span :class="['badge', item.trend]">{{ item.trend }}</span>
              </td>
              <td>{{ item.gap }}</td>
              <td>
                <strong>{{ item.quantity }}</strong>
                <span v-if="item.quantity < item.gap" class="partial-label"> (partial)</span>
              </td>
              <td>{{ formatCurrency(item.unit_price) }}</td>
              <td>{{ formatCurrency(item.subtotal) }}</td>
              <td>
                <span :class="['badge', leadTimeBadgeClass(item.lead_time_days)]">
                  {{ item.lead_time_days }}d
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Budget Usage Bar -->
      <div class="budget-usage">
        <div class="budget-usage-text">
          Budget used: <strong>{{ formatCurrency(budgetUsed) }}</strong> of <strong>{{ formattedBudget }}</strong>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: budgetUsedPercent + '%' }"
            :class="progressColorClass"
          ></div>
        </div>
        <div class="budget-usage-percent">{{ budgetUsedPercent }}% utilized</div>
      </div>
    </div>

    <!-- Place Order Button -->
    <div class="action-row">
      <button
        class="place-order-btn"
        :disabled="recommendations.length === 0 || submitting"
        @click="placeOrder"
      >
        <span v-if="submitting">Placing order...</span>
        <span v-else>Place Order</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const BUDGET_MIN = 1000
const BUDGET_MAX = 100000
const BUDGET_STEP = 1000

const LEAD_TIME_MAP = {
  increasing: 7,
  stable: 14,
  decreasing: 21
}

export default {
  name: 'Restocking',
  setup() {
    const router = useRouter()
    const { t } = useI18n()

    const budget = ref(25000)
    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)
    const submitError = ref(null)

    // Greedy budget allocation algorithm
    const recommendations = computed(() => {
      const items = forecasts.value
        .filter(f => (f.forecasted_demand - f.current_demand) > 0)
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          gap: f.forecasted_demand - f.current_demand,
          unit_cost: f.unit_cost
        }))
        .sort((a, b) => b.gap - a.gap)

      const result = []
      let budgetRemaining = budget.value

      for (const item of items) {
        if (budgetRemaining <= 0) break

        const full_cost = item.gap * item.unit_cost

        if (full_cost <= budgetRemaining) {
          result.push({
            sku: item.sku,
            name: item.name,
            trend: item.trend,
            gap: item.gap,
            quantity: item.gap,
            unit_price: item.unit_cost,
            subtotal: full_cost,
            lead_time_days: LEAD_TIME_MAP[item.trend] ?? 14
          })
          budgetRemaining -= full_cost
        } else {
          const partialQty = Math.floor(budgetRemaining / item.unit_cost)
          if (partialQty > 0) {
            const subtotal = partialQty * item.unit_cost
            result.push({
              sku: item.sku,
              name: item.name,
              trend: item.trend,
              gap: item.gap,
              quantity: partialQty,
              unit_price: item.unit_cost,
              subtotal,
              lead_time_days: LEAD_TIME_MAP[item.trend] ?? 14
            })
            budgetRemaining -= subtotal
          }
          break
        }
      }

      return result
    })

    const budgetUsed = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.subtotal, 0)
    })

    const budgetUsedPercent = computed(() => {
      if (budget.value === 0) return 0
      return Math.min(100, Math.round((budgetUsed.value / budget.value) * 100))
    })

    const progressColorClass = computed(() => {
      const pct = budgetUsedPercent.value
      if (pct > 95) return 'progress-red'
      if (pct >= 80) return 'progress-amber'
      return 'progress-green'
    })

    const formattedBudget = computed(() => formatCurrency(budget.value))

    function formatCurrency(value) {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
    }

    function leadTimeBadgeClass(days) {
      if (days === 7) return 'success'
      if (days === 14) return 'info'
      return 'warning'
    }

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + (err.message || 'Unknown error')
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return

      submitting.value = true
      submitError.value = null
      successMessage.value = null

      try {
        const payload = {
          items: recommendations.value.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.quantity,
            unit_price: item.unit_price,
            trend: item.trend
          })),
          warehouse: 'San Francisco',
          budget: budget.value
        }

        const result = await api.createRestockOrder(payload)

        successMessage.value = `Order ${result.order_number} placed successfully! Redirecting to Orders...`

        setTimeout(() => {
          router.push('/orders')
        }, 2000)
      } catch (err) {
        submitError.value = 'Failed to place order: ' + (err.message || 'Unknown error')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      loading,
      error,
      submitting,
      successMessage,
      submitError,
      recommendations,
      budgetUsed,
      budgetUsedPercent,
      progressColorClass,
      formattedBudget,
      formatCurrency,
      leadTimeBadgeClass,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

/* Budget slider section */
.slider-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.budget-display {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
  transition: box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 1px 8px rgba(37, 99, 235, 0.6);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
}

/* Item count badge in card header */
.item-count {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
  background: #f1f5f9;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
}

/* Partial order label */
.partial-label {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 400;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Budget usage bar */
.budget-usage {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-usage-text {
  font-size: 0.938rem;
  color: #334155;
}

.budget-usage-text strong {
  color: #0f172a;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.progress-fill.progress-green {
  background: #10b981;
}

.progress-fill.progress-amber {
  background: #f59e0b;
}

.progress-fill.progress-red {
  background: #ef4444;
}

.budget-usage-percent {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
}

/* Place order button row */
.action-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.place-order-btn {
  padding: 0.75rem 2rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease;
  letter-spacing: 0.01em;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
