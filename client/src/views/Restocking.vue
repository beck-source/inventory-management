<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget to get AI-recommended restocking orders based on demand forecasts.</p>
    </div>

    <!-- Budget Slider -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Restocking Budget</h3>
      </div>
      <div class="budget-section">
        <div class="budget-display">
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          max="100000"
          step="1000"
          :value="budget"
          @input="onSliderInput"
        />
        <div class="budget-ticks">
          <span>$0</span>
          <span>$25,000</span>
          <span>$50,000</span>
          <span>$75,000</span>
          <span>$100,000</span>
        </div>
        <div v-if="recommendations" class="budget-meta">
          <div class="budget-meta-item">
            <span class="meta-label">Total Recommended Cost</span>
            <span class="meta-value">{{ formatCurrency(recommendations.total_cost) }}</span>
          </div>
          <div class="budget-meta-item">
            <span class="meta-label">Remaining Budget</span>
            <span
              class="meta-value"
              :class="recommendations.remaining_budget < 0 ? 'text-danger' : 'text-success'"
            >
              {{ formatCurrency(recommendations.remaining_budget) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Recommendations Table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          Recommended Items
          <span v-if="recommendations" class="item-count">({{ recommendations.items.length }})</span>
        </h3>
      </div>

      <div v-if="budget === 0 && !recommendations" class="empty-state">
        Use the slider to set your budget and see restocking recommendations.
      </div>

      <div v-else-if="loading" class="loading">Loading recommendations...</div>

      <div v-else-if="error" class="error">{{ error }}</div>

      <div v-else-if="recommendations && recommendations.items.length === 0" class="empty-state">
        No recommendations available for this budget.
      </div>

      <div v-else-if="recommendations" class="table-container">
        <table>
          <thead>
            <tr>
              <th>Item Name</th>
              <th>SKU</th>
              <th>Warehouse</th>
              <th>Trend</th>
              <th>Qty to Order</th>
              <th>Unit Cost</th>
              <th>Total Cost</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in sortedItems"
              :key="item.item_sku"
              :class="item.selected ? 'row-selected' : 'row-overbudget'"
            >
              <td>
                <strong>{{ item.item_name }}</strong>
              </td>
              <td class="sku-cell">{{ item.item_sku }}</td>
              <td>{{ item.warehouse }}</td>
              <td>
                <span :class="['badge', item.trend.toLowerCase()]">{{ item.trend }}</span>
              </td>
              <td>{{ item.quantity_to_order.toLocaleString() }}</td>
              <td>{{ formatCurrency(item.unit_cost) }}</td>
              <td><strong>{{ formatCurrency(item.item_cost) }}</strong></td>
              <td>
                <span v-if="item.selected" class="badge success">Selected</span>
                <span v-else class="badge muted">Over budget</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Order Summary + Place Order -->
    <div v-if="selectedItems.length > 0" class="card">
      <div class="card-header">
        <h3 class="card-title">Order Summary</h3>
      </div>

      <div v-if="placedOrder" class="success-banner">
        <div class="success-icon">&#10003;</div>
        <div class="success-content">
          <strong>Order {{ placedOrder.order_number }} placed successfully</strong>
          — expected delivery in 14 days.
          <router-link to="/orders" class="view-orders-link">View in Orders</router-link>
        </div>
      </div>

      <div v-else>
        <div class="summary-items">
          <div
            v-for="item in selectedItems"
            :key="item.item_sku"
            class="summary-item"
          >
            <span class="summary-item-name">{{ item.item_name }}</span>
            <span class="summary-item-detail">Qty: {{ item.quantity_to_order.toLocaleString() }}</span>
            <span class="summary-item-cost">{{ formatCurrency(item.item_cost) }}</span>
          </div>
        </div>

        <div class="summary-total">
          <span class="total-label">Total Cost</span>
          <span class="total-value">{{ formatCurrency(selectedItemsTotal) }}</span>
        </div>

        <button
          class="place-order-btn"
          :disabled="placing"
          @click="placeOrder"
        >
          {{ placing ? 'Placing Order...' : 'Place Order' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(0)
    const recommendations = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const placing = ref(false)
    const placedOrder = ref(null)

    let debounceTimer = null

    const formatCurrency = (value) => {
      if (value == null) return '$0'
      return '$' + Number(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    }

    const selectedItems = computed(() => {
      if (!recommendations.value) return []
      return recommendations.value.items.filter(i => i.selected)
    })

    const selectedItemsTotal = computed(() => {
      return selectedItems.value.reduce((sum, i) => sum + i.item_cost, 0)
    })

    const sortedItems = computed(() => {
      if (!recommendations.value) return []
      const selected = recommendations.value.items.filter(i => i.selected)
      const overBudget = recommendations.value.items.filter(i => !i.selected)
      return [...selected, ...overBudget]
    })

    const fetchRecommendations = async (value) => {
      if (value === 0) {
        recommendations.value = null
        return
      }
      loading.value = true
      error.value = null
      try {
        recommendations.value = await api.getRestockingRecommendations(value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const onSliderInput = (event) => {
      budget.value = Number(event.target.value)
      placedOrder.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        fetchRecommendations(budget.value)
      }, 300)
    }

    const placeOrder = async () => {
      if (placing.value || selectedItems.value.length === 0) return
      placing.value = true
      error.value = null
      try {
        const order = await api.placeRestockingOrder(selectedItems.value)
        placedOrder.value = order
        // Reset after success
        budget.value = 0
        recommendations.value = null
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error(err)
      } finally {
        placing.value = false
      }
    }

    return {
      budget,
      recommendations,
      loading,
      error,
      placing,
      placedOrder,
      selectedItems,
      selectedItemsTotal,
      sortedItems,
      formatCurrency,
      onSliderInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

/* Budget Section */
.budget-section {
  padding: 0.5rem 0;
}

.budget-display {
  text-align: center;
  margin-bottom: 1.25rem;
}

.budget-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.04em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  accent-color: #2563eb;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #2563eb;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
  transition: box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #2563eb;
  border-radius: 50%;
  border: none;
  cursor: pointer;
}

.budget-ticks {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
}

.budget-meta {
  display: flex;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.budget-meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.meta-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.text-success {
  color: #059669;
}

.text-danger {
  color: #dc2626;
}

/* Table rows */
.row-selected {
  background: #f0fdf4;
}

.row-selected:hover {
  background: #dcfce7 !important;
}

.row-overbudget {
  opacity: 0.5;
  cursor: not-allowed;
}

.row-overbudget:hover {
  background: inherit !important;
}

.sku-cell {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.8rem;
  color: #64748b;
}

/* Muted badge */
.badge.muted {
  background: #f1f5f9;
  color: #64748b;
}

/* Empty state */
.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.item-count {
  font-weight: 400;
  color: #64748b;
  font-size: 0.938rem;
  margin-left: 0.25rem;
}

/* Order Summary */
.summary-items {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin-bottom: 1.25rem;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.625rem 0.75rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.summary-item-name {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.summary-item-detail {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
}

.summary-item-cost {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
}

.summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 0.75rem;
  border-top: 2px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.total-label {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.place-order-btn {
  width: 100%;
  padding: 0.875rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Success Banner */
.success-banner {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
}

.success-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  background: #059669;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 700;
}

.success-content {
  font-size: 0.938rem;
  color: #065f46;
  line-height: 1.5;
}

.view-orders-link {
  display: inline-block;
  margin-left: 0.5rem;
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
}

.view-orders-link:hover {
  text-decoration: underline;
}
</style>
