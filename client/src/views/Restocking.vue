<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Review demand gaps and place restocking orders within budget.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Success banner -->
      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
      </div>

      <!-- Budget slider section -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
        </div>
        <div class="budget-controls">
          <div class="slider-row">
            <span class="budget-label">Budget:</span>
            <input
              type="range"
              min="0"
              max="100000"
              step="1000"
              v-model.number="budget"
              class="budget-slider"
            />
            <span class="budget-value">{{ formatCurrency(budget) }}</span>
          </div>
          <div class="budget-remaining" :class="{ over: budgetRemaining < 0 }">
            Budget remaining: <strong>{{ formatCurrency(budgetRemaining) }}</strong>
          </div>
        </div>
      </div>

      <!-- Recommendations table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Restocking Recommendations ({{ eligibleItems.length }} items)</h3>
        </div>

        <div v-if="budgetWarning" class="budget-warning">
          Warning: Selected items exceed your budget by {{ formatCurrency(-budgetRemaining) }}.
        </div>

        <div class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">SKU</th>
                <th class="col-name">Item Name</th>
                <th class="col-trend">Trend</th>
                <th class="col-gap">Gap (Qty)</th>
                <th class="col-cost">Unit Cost</th>
                <th class="col-total">Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in eligibleItems" :key="item.item_sku">
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(item.item_sku)"
                    @change="toggleItem(item)"
                  />
                </td>
                <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-trend">
                  <span :class="['badge', getTrendClass(item.trend)]">{{ item.trend }}</span>
                </td>
                <td class="col-gap">{{ item.demand_gap }}</td>
                <td class="col-cost">{{ formatCurrency(item.unit_cost) }}</td>
                <td class="col-total"><strong>{{ formatCurrency(item.line_total) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="table-footer">
          <span class="total-label">Total cost of selected items:</span>
          <span class="total-value" :class="{ over: budgetRemaining < 0 }">
            {{ formatCurrency(selectedTotal) }}
          </span>
        </div>
      </div>

      <!-- Place Order button -->
      <div class="order-actions">
        <button
          class="btn-primary"
          :disabled="selectedSkus.size === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Submitting...' : 'Place Order' }}
        </button>
        <span v-if="selectedSkus.size === 0" class="action-hint">Select at least one item to place an order.</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)
    const demandItems = ref([])
    const budget = ref(50000)
    const selectedSkus = ref(new Set())

    // Items with demand_gap > 0, sorted descending
    const eligibleItems = computed(() => {
      return demandItems.value
        .filter(item => (item.forecasted_demand - item.current_demand) > 0)
        .map(item => ({
          ...item,
          demand_gap: item.forecasted_demand - item.current_demand,
          line_total: item.unit_cost * (item.forecasted_demand - item.current_demand)
        }))
        .sort((a, b) => b.demand_gap - a.demand_gap)
    })

    const selectedTotal = computed(() => {
      return eligibleItems.value
        .filter(item => selectedSkus.value.has(item.item_sku))
        .reduce((sum, item) => sum + item.line_total, 0)
    })

    const budgetRemaining = computed(() => budget.value - selectedTotal.value)

    const budgetWarning = computed(() => budgetRemaining.value < 0)

    // Auto-select items greedily when budget or eligible items change
    const autoSelect = () => {
      const newSelected = new Set()
      let remaining = budget.value

      for (const item of eligibleItems.value) {
        if (item.line_total <= remaining) {
          newSelected.add(item.item_sku)
          remaining -= item.line_total
        }
      }

      selectedSkus.value = newSelected
    }

    watch(budget, autoSelect)

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        demandItems.value = await api.getDemandForecasts()
        autoSelect()
      } catch (err) {
        error.value = 'Failed to load demand data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const toggleItem = (item) => {
      const next = new Set(selectedSkus.value)
      if (next.has(item.item_sku)) {
        next.delete(item.item_sku)
      } else {
        next.add(item.item_sku)
      }
      selectedSkus.value = next
    }

    const placeOrder = async () => {
      submitting.value = true
      successMessage.value = null
      try {
        const items = eligibleItems.value
          .filter(item => selectedSkus.value.has(item.item_sku))
          .map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.demand_gap,
            unit_cost: item.unit_cost,
            line_total: item.line_total
          }))

        const result = await api.createRestockingOrder(items)
        const deliveryDate = new Date(result.expected_delivery)
        const formattedDate = isNaN(deliveryDate.getTime())
          ? result.expected_delivery
          : deliveryDate.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })

        successMessage.value = `Order ${result.order_number} submitted. Delivery expected by ${formattedDate}.`
        selectedSkus.value = new Set()
        autoSelect()
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const formatCurrency = (value) => {
      return '$' + Math.round(value).toLocaleString('en-US')
    }

    const getTrendClass = (trend) => {
      const map = { increasing: 'increasing', stable: 'stable', decreasing: 'decreasing' }
      return map[trend] || 'info'
    }

    onMounted(loadData)

    return {
      loading,
      error,
      submitting,
      successMessage,
      budget,
      eligibleItems,
      selectedSkus,
      selectedTotal,
      budgetRemaining,
      budgetWarning,
      toggleItem,
      placeOrder,
      formatCurrency,
      getTrendClass
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
  min-width: 60px;
}

.budget-slider {
  flex: 1;
  max-width: 400px;
  accent-color: #2563eb;
  cursor: pointer;
  height: 4px;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 100px;
}

.budget-remaining {
  font-size: 0.938rem;
  color: #64748b;
}

.budget-remaining strong {
  color: #059669;
}

.budget-remaining.over strong {
  color: #dc2626;
}

.budget-warning {
  background: #fef9c3;
  border: 1px solid #fde047;
  color: #713f12;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-check { width: 40px; }
.col-sku { width: 120px; }
.col-name { width: auto; }
.col-trend { width: 110px; }
.col-gap { width: 90px; }
.col-cost { width: 100px; }
.col-total { width: 110px; }

input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

.table-footer {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 0.75rem;
  border-top: 2px solid #e2e8f0;
  margin-top: 0.25rem;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.total-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.total-value.over {
  color: #dc2626;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0 1.5rem;
}

.btn-primary {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.action-hint {
  font-size: 0.875rem;
  color: #64748b;
}
</style>
