<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your available budget to see which items to restock based on demand forecasts.</p>
    </div>

    <div v-if="loading" class="loading">Loading demand forecasts...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="slider-wrapper">
          <span class="slider-label">$0</span>
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="500000"
            step="1000"
            class="budget-slider"
          />
          <span class="slider-label">$500,000</span>
        </div>
      </div>

      <!-- Budget Summary -->
      <div class="stats-grid" v-if="recommendedItems.length > 0 || orderSuccess">
        <div class="stat-card info">
          <div class="stat-label">Allocated</div>
          <div class="stat-value">${{ allocatedBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Items Recommended</div>
          <div class="stat-value">{{ recommendedItems.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Remaining</div>
          <div class="stat-value">${{ remainingBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</div>
        </div>
      </div>

      <!-- Success message -->
      <div v-if="orderSuccess" class="success-banner">
        Order <strong>{{ submittedOrderNumber }}</strong> placed successfully.
        Expected delivery: <strong>{{ submittedDelivery }}</strong>.
      </div>

      <!-- Recommended Items -->
      <div class="card" v-if="!orderSuccess">
        <div class="card-header">
          <h3 class="card-title">Recommended Restocking ({{ recommendedItems.length }} items)</h3>
        </div>

        <div v-if="recommendedItems.length === 0" class="empty-state">
          No items can be restocked within this budget. Try increasing the budget.
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Demand Gap</th>
                <th>Unit Cost</th>
                <th>Restock Qty</th>
                <th>Line Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.item_sku">
                <td><code>{{ item.item_sku }}</code></td>
                <td>{{ item.item_name }}</td>
                <td>+{{ item.gap }}</td>
                <td>${{ item.unit_cost.toFixed(2) }}</td>
                <td>{{ item.gap }}</td>
                <td><strong>${{ item.lineTotal.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</strong></td>
                <td>
                  <button class="btn-remove" @click="excludeItem(item.item_sku)" title="Remove">&#x2715;</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer" v-if="recommendedItems.length > 0">
          <div v-if="!confirmingOrder">
            <button class="btn-primary" @click="confirmingOrder = true">Place Order</button>
          </div>
          <div v-else class="confirm-row">
            <span>Place restocking order for {{ recommendedItems.length }} items totalling ${{ allocatedBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}?</span>
            <button class="btn-primary" @click="placeOrder" :disabled="submitting">
              {{ submitting ? 'Submitting...' : 'Confirm' }}
            </button>
            <button class="btn-secondary" @click="confirmingOrder = false" :disabled="submitting">Cancel</button>
          </div>
          <div v-if="submitError" class="error">{{ submitError }}</div>
        </div>
      </div>

      <!-- Over Budget Items -->
      <div class="card over-budget-card" v-if="overBudgetItems.length > 0 && !orderSuccess">
        <details>
          <summary class="card-title">Over Budget ({{ overBudgetItems.length }} items not included)</summary>
          <div class="table-container" style="margin-top: 12px;">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Demand Gap</th>
                  <th>Unit Cost</th>
                  <th>Would Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in overBudgetItems" :key="item.item_sku">
                  <td><code>{{ item.item_sku }}</code></td>
                  <td>{{ item.item_name }}</td>
                  <td>+{{ item.gap }}</td>
                  <td>${{ item.unit_cost.toFixed(2) }}</td>
                  <td>${{ item.lineTotal.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
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
    const forecasts = ref([])
    const budget = ref(100000)
    const excludedSkus = ref(new Set())
    const confirmingOrder = ref(false)
    const submitting = ref(false)
    const submitError = ref(null)
    const orderSuccess = ref(false)
    const submittedOrderNumber = ref('')
    const submittedDelivery = ref('')

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Items with a positive demand gap, sorted by gap descending
    const candidateItems = computed(() => {
      return forecasts.value
        .filter(f => f.forecasted_demand > f.current_demand && !excludedSkus.value.has(f.item_sku))
        .map(f => ({
          ...f,
          gap: f.forecasted_demand - f.current_demand,
          lineTotal: (f.forecasted_demand - f.current_demand) * f.unit_cost,
        }))
        .sort((a, b) => b.gap - a.gap)
    })

    // Greedy allocation: add items until budget is exhausted
    const allocation = computed(() => {
      let remaining = budget.value
      const recommended = []
      const overBudget = []
      for (const item of candidateItems.value) {
        if (item.lineTotal <= remaining) {
          recommended.push(item)
          remaining -= item.lineTotal
        } else {
          overBudget.push(item)
        }
      }
      return { recommended, overBudget }
    })

    const recommendedItems = computed(() => allocation.value.recommended)
    const overBudgetItems = computed(() => allocation.value.overBudget)
    const allocatedBudget = computed(() => recommendedItems.value.reduce((s, i) => s + i.lineTotal, 0))
    const remainingBudget = computed(() => budget.value - allocatedBudget.value)

    const excludeItem = (sku) => {
      excludedSkus.value = new Set([...excludedSkus.value, sku])
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const items = recommendedItems.value.map(i => ({
          sku: i.item_sku,
          name: i.item_name,
          quantity: i.gap,
          unit_cost: i.unit_cost,
        }))
        const order = await api.submitRestockingOrder(items)
        submittedOrderNumber.value = order.order_number
        submittedDelivery.value = new Date(order.expected_delivery).toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        })
        orderSuccess.value = true
        confirmingOrder.value = false
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      loading,
      error,
      budget,
      recommendedItems,
      overBudgetItems,
      allocatedBudget,
      remainingBudget,
      excludeItem,
      confirmingOrder,
      submitting,
      submitError,
      orderSuccess,
      submittedOrderNumber,
      submittedDelivery,
      placeOrder,
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 4px;
}
.page-header p {
  color: #64748b;
  font-size: 0.9rem;
}

.budget-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.budget-display {
  font-size: 1.4rem;
  font-weight: 700;
  color: #60a5fa;
}
.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}
.slider-label {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
}
.budget-slider {
  flex: 1;
  height: 4px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.success-banner {
  background: #14432a;
  border: 1px solid #22c55e;
  border-radius: 8px;
  padding: 16px 20px;
  color: #4ade80;
  margin-bottom: 20px;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #64748b;
}

.card-footer {
  padding: 16px 20px;
  border-top: 1px solid #334155;
  margin-top: 8px;
}
.confirm-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.confirm-row span {
  color: #94a3b8;
  font-size: 0.875rem;
}

.btn-primary {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-secondary {
  background: transparent;
  color: #94a3b8;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 0.875rem;
  cursor: pointer;
}
.btn-secondary:hover:not(:disabled) {
  background: #1e293b;
}
.btn-remove {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 2px 6px;
  border-radius: 4px;
}
.btn-remove:hover {
  color: #ef4444;
  background: #2d1f1f;
}

.over-budget-card details summary {
  cursor: pointer;
  padding: 4px 0;
  color: #94a3b8;
}
.over-budget-card details summary::-webkit-details-marker {
  color: #64748b;
}

code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  background: #0f172a;
  color: #7dd3fc;
  padding: 2px 6px;
  border-radius: 4px;
}

.error {
  color: #f87171;
  padding: 8px 0;
  font-size: 0.875rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
thead th {
  text-align: left;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 10px 14px;
  border-bottom: 1px solid #334155;
}
tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid #1e293b;
  color: #cbd5e1;
}
tbody tr:last-child td {
  border-bottom: none;
}
tbody tr:hover td {
  background: #243047;
}
</style>
