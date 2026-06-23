<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Recommendations</h2>
      <p>Set a budget and get item recommendations based on demand growth forecasts and current stock levels.</p>
    </div>

    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="allItems.length === 0" class="empty-state">
      No restocking needed — all items are above their reorder points.
    </div>
    <div v-else>

      <!-- Budget slider -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-controls">
          <div class="budget-display">
            <span class="budget-amount">${{ budget.toLocaleString() }}</span>
            <span class="budget-remaining" :class="{ 'over-budget': remainingBudget < 0 }">
              {{ remainingBudget >= 0
                ? `$${remainingBudget.toLocaleString()} remaining`
                : `$${Math.abs(remainingBudget).toLocaleString()} over budget` }}
            </span>
          </div>
          <input
            type="range"
            class="budget-slider"
            :min="0"
            :max="maxBudget"
            :step="sliderStep"
            v-model.number="budget"
          />
          <div class="slider-labels">
            <span>$0</span>
            <span>${{ maxBudget.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Items
            <span class="item-count">({{ allItems.length }} items · ${{ selectedTotal.toLocaleString() }} selected)</span>
          </h3>
          <div class="header-actions">
            <button class="btn-secondary" @click="selectAll">Select All</button>
            <button class="btn-secondary" @click="selectNone">Deselect All</button>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No items fit within this budget. Try increasing the budget.
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">SKU</th>
                <th class="col-name">Item</th>
                <th class="col-category">Category</th>
                <th class="col-trend">Demand Growth</th>
                <th class="col-qty">Rec. Qty</th>
                <th class="col-cost">Unit Cost</th>
                <th class="col-total">Est. Cost</th>
                <th class="col-lead">Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.sku"
                :class="{ 'row-selected': selectedSkus.has(item.sku) }"
                @click="toggleItem(item)"
              >
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(item.sku)"
                    @change.stop="toggleItem(item)"
                  />
                </td>
                <td class="col-sku"><code>{{ item.sku }}</code></td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-category">{{ item.category }}</td>
                <td class="col-trend">
                  <span class="badge increasing">+{{ item.demand_growth_pct.toFixed(1) }}%</span>
                </td>
                <td class="col-qty">{{ item.recommended_qty.toLocaleString() }}</td>
                <td class="col-cost">${{ item.unit_cost.toFixed(2) }}</td>
                <td class="col-total"><strong>${{ item.estimated_cost.toLocaleString() }}</strong></td>
                <td class="col-lead">{{ item.lead_days }} days</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Place Order button -->
        <div class="order-footer">
          <div class="order-summary" v-if="selectedSkus.size > 0">
            {{ selectedSkus.size }} item{{ selectedSkus.size !== 1 ? 's' : '' }} selected &mdash;
            Total: <strong>${{ selectedTotal.toLocaleString() }}</strong>
          </div>
          <button
            class="btn-primary"
            :disabled="selectedSkus.size === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
      </div>

      <!-- Success confirmation -->
      <div v-if="lastOrder" class="success-banner">
        <div class="success-icon">✓</div>
        <div class="success-details">
          <strong>Order {{ lastOrder.order_number }} placed successfully.</strong>
          Expected delivery in {{ lastOrder.lead_time_days }} days
          ({{ formatDate(lastOrder.expected_delivery) }}).
          <router-link to="/orders" class="view-link">View in Orders tab</router-link>
        </div>
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
    const submitting = ref(false)
    const lastOrder = ref(null)

    const budget = ref(0)
    const allItems = ref([])
    const selectedSkus = ref(new Set())

    const maxBudget = computed(() =>
      allItems.value.reduce((sum, i) => sum + i.estimated_cost, 0)
    )

    const sliderStep = computed(() => {
      const max = maxBudget.value
      if (max <= 1000) return 10
      if (max <= 10000) return 100
      return 500
    })

    // Greedy fill: include items (sorted by demand_growth_pct desc by backend) until budget exceeded
    const recommendations = computed(() => {
      let cumulative = 0
      const result = []
      for (const item of allItems.value) {
        if (cumulative + item.estimated_cost <= budget.value) {
          cumulative += item.estimated_cost
          result.push(item)
        }
      }
      return result
    })

    const selectedItems = computed(() =>
      recommendations.value.filter(i => selectedSkus.value.has(i.sku))
    )

    const selectedTotal = computed(() =>
      selectedItems.value.reduce((sum, i) => sum + i.estimated_cost, 0)
    )

    const remainingBudget = computed(() => budget.value - selectedTotal.value)

    const toggleItem = (item) => {
      const next = new Set(selectedSkus.value)
      if (next.has(item.sku)) {
        next.delete(item.sku)
      } else {
        next.add(item.sku)
      }
      selectedSkus.value = next
    }

    const selectAll = () => {
      selectedSkus.value = new Set(recommendations.value.map(i => i.sku))
    }

    const selectNone = () => {
      selectedSkus.value = new Set()
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return
      submitting.value = true
      lastOrder.value = null
      try {
        const payload = selectedItems.value.map(i => ({
          sku: i.sku,
          name: i.item_name,
          category: i.category,
          quantity: i.recommended_qty,
          unit_cost: i.unit_cost,
        }))
        lastOrder.value = await api.submitRestockingOrder(payload, selectedTotal.value)
        selectedSkus.value = new Set()
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateStr) => {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      })
    }

    onMounted(async () => {
      try {
        allItems.value = await api.getRestockingRecommendations()
        budget.value = maxBudget.value
        // Auto-select all items within the initial (max) budget
        selectedSkus.value = new Set(allItems.value.map(i => i.sku))
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    })

    return {
      loading,
      error,
      submitting,
      lastOrder,
      budget,
      allItems,
      maxBudget,
      sliderStep,
      recommendations,
      selectedSkus,
      selectedTotal,
      remainingBudget,
      toggleItem,
      selectAll,
      selectNone,
      placeOrder,
      formatDate,
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-display {
  display: flex;
  align-items: baseline;
  gap: 1rem;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-remaining {
  font-size: 0.875rem;
  color: #059669;
  font-weight: 500;
}

.budget-remaining.over-budget {
  color: #dc2626;
}

.budget-slider {
  width: 100%;
  max-width: 600px;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  max-width: 600px;
  font-size: 0.75rem;
  color: #94a3b8;
}

.item-count {
  font-size: 0.875rem;
  font-weight: 400;
  color: #64748b;
  margin-left: 0.5rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-secondary {
  padding: 0.375rem 0.875rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #475569;
  font-size: 0.813rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-check    { width: 40px; }
.col-sku      { width: 110px; }
.col-name     { width: auto; }
.col-category { width: 140px; }
.col-trend    { width: 130px; }
.col-qty      { width: 100px; }
.col-cost     { width: 110px; }
.col-total    { width: 120px; }
.col-lead     { width: 90px; }

.restock-table tbody tr {
  cursor: pointer;
}

.row-selected {
  background: #eff6ff !important;
}

code {
  font-family: 'SF Mono', 'Fira Mono', monospace;
  font-size: 0.813rem;
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
}

.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.938rem;
}

.order-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1.25rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.order-summary {
  font-size: 0.875rem;
  color: #64748b;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.success-banner {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-top: 0.5rem;
}

.success-icon {
  font-size: 1.25rem;
  color: #059669;
  font-weight: 700;
  flex-shrink: 0;
}

.success-details {
  font-size: 0.875rem;
  color: #065f46;
  line-height: 1.6;
}

.view-link {
  color: #059669;
  font-weight: 600;
  margin-left: 0.5rem;
  text-decoration: underline;
}
</style>
