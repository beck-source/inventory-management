<template>
  <div class="restocking">
    <!-- Page Header -->
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Auto-select items to restock based on demand trends and your available budget</p>
    </div>

    <div v-if="loading" class="loading">Loading demand forecasts...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Success state after order placed -->
    <div v-else-if="orderSuccess" class="card success-card">
      <div class="success-content">
        <div class="success-icon-wrap">✓</div>
        <h3>Order Placed Successfully</h3>
        <p>Order Number: <strong>{{ submittedOrderNumber }}</strong></p>
        <p>{{ selectedItems.length }} items · Total: ${{ totalCost.toLocaleString() }}</p>
        <p>Expected delivery in 14 days: <strong>{{ expectedDeliveryDate }}</strong></p>
        <p class="hint-text">Navigate to the Orders tab to view your restocking order.</p>
        <button class="btn-secondary" @click="resetOrder">Plan Another Order</button>
      </div>
    </div>

    <!-- Main planner UI -->
    <div v-else>
      <!-- Budget Slider Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="slider-wrap">
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="200000"
            step="5000"
            class="budget-slider"
          />
          <div class="slider-labels">
            <span>$0</span>
            <span>$50k</span>
            <span>$100k</span>
            <span>$150k</span>
            <span>$200k</span>
          </div>
        </div>
      </div>

      <!-- Stats Row -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Budget</div>
          <div class="stat-value">${{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Est. Order Total</div>
          <div class="stat-value">${{ totalCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Items Selected</div>
          <div class="stat-value">{{ selectedItems.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Remaining Budget</div>
          <div class="stat-value">${{ remainingBudget.toLocaleString() }}</div>
        </div>
      </div>

      <!-- Recommended Items Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ selectedItems.length }} of {{ eligibleItems.length }} eligible)</h3>
        </div>
        <div v-if="selectedItems.length === 0" class="empty-state">
          <p>Increase your budget to see recommended items.</p>
          <p class="hint-text">Items with increasing demand are prioritized first.</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Qty to Order</th>
                <th>Unit Cost</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedItems" :key="item.id">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td><span :class="['badge', item.trend]">{{ item.trend }}</span></td>
                <td>{{ item.restock_quantity.toLocaleString() }}</td>
                <td>${{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>${{ (item.unit_cost * item.restock_quantity).toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Skipped Items -->
      <div v-if="skippedItems.length > 0" class="card">
        <div class="card-header">
          <h3 class="card-title">Not Selected ({{ skippedItems.length }})</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Qty</th>
                <th>Line Total</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in skippedItems" :key="item.id" class="skipped-row">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td><span :class="['badge', item.trend]">{{ item.trend }}</span></td>
                <td>{{ item.restock_quantity.toLocaleString() }}</td>
                <td>${{ (item.unit_cost * item.restock_quantity).toLocaleString() }}</td>
                <td class="reason-cell">
                  <span v-if="item.trend === 'decreasing'" class="reason-badge reason-trend">Decreasing demand</span>
                  <span v-else class="reason-badge reason-budget">Over budget</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Place Order Button -->
      <div class="order-actions">
        <button
          class="btn-primary"
          :disabled="selectedItems.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Placing Order...' : `Place Order — $${totalCost.toLocaleString()}` }}
        </button>
        <p v-if="selectedItems.length === 0" class="hint-text">Adjust the budget slider to select items</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const budget = ref(50000)
    const submitting = ref(false)
    const orderSuccess = ref(false)
    const submittedOrderNumber = ref('')

    // Items eligible for restock (not decreasing), sorted increasing first then stable
    const eligibleItems = computed(() => {
      return allForecasts.value
        .filter(item => item.trend !== 'decreasing')
        .sort((a, b) => {
          const priority = { increasing: 0, stable: 1 }
          return priority[a.trend] - priority[b.trend]
        })
    })

    // Greedy selection: iterate eligibleItems in priority order, add each item that fits
    const selectedItems = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const item of eligibleItems.value) {
        const itemCost = item.unit_cost * item.restock_quantity
        if (remaining >= itemCost) {
          selected.push(item)
          remaining -= itemCost
        }
      }
      return selected
    })

    // Items NOT selected (either decreasing trend or didn't fit in budget)
    const skippedItems = computed(() => {
      const selectedIds = new Set(selectedItems.value.map(i => i.id))
      return allForecasts.value.filter(item => !selectedIds.has(item.id))
    })

    const totalCost = computed(() =>
      selectedItems.value.reduce((sum, item) => sum + (item.unit_cost * item.restock_quantity), 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const expectedDeliveryDate = computed(() => {
      const d = new Date()
      d.setDate(d.getDate() + 14)
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        allForecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return
      submitting.value = true
      try {
        const orderData = {
          items: selectedItems.value.map(item => ({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.restock_quantity,
            unit_price: item.unit_cost
          })),
          total_value: totalCost.value
        }
        const result = await api.createRestockingOrder(orderData)
        submittedOrderNumber.value = result.order_number
        orderSuccess.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const resetOrder = () => {
      orderSuccess.value = false
      submittedOrderNumber.value = ''
      budget.value = 50000
    }

    onMounted(loadForecasts)

    return {
      loading,
      error,
      allForecasts,
      budget,
      submitting,
      orderSuccess,
      submittedOrderNumber,
      eligibleItems,
      selectedItems,
      skippedItems,
      totalCost,
      remainingBudget,
      expectedDeliveryDate,
      loadForecasts,
      placeOrder,
      resetOrder
    }
  }
}
</script>

<style scoped>
.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.slider-wrap {
  padding: 0.5rem 0 0.25rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  appearance: none;
  -webkit-appearance: none;
  background: linear-gradient(to right, #2563eb calc(var(--val, 25) * 1%), #e2e8f0 calc(var(--val, 25) * 1%));
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.hint-text {
  font-size: 0.875rem;
  color: #64748b;
  margin-top: 0.5rem;
}

.order-actions {
  margin-top: 0.5rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #2563eb;
  border: 1px solid #2563eb;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #eff6ff;
}

.success-card {
  border-left: 4px solid #059669;
}

.success-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.success-icon-wrap {
  width: 48px;
  height: 48px;
  background: #d1fae5;
  color: #059669;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.success-content h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.success-content p {
  color: #334155;
  font-size: 0.938rem;
}

.skipped-row td {
  color: #94a3b8;
}

.reason-badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.reason-trend {
  background: #fecaca;
  color: #991b1b;
}

.reason-budget {
  background: #fef3c7;
  color: #92400e;
}
</style>
