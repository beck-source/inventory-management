<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Budget-aware recommendations based on low stock and increasing demand</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Success banner -->
      <div v-if="submittedOrder" class="success-banner">
        <div class="success-banner-text">
          <strong>Order {{ submittedOrder.order_number }} submitted successfully.</strong>
          Delivery in 14 days.
        </div>
        <button class="btn-secondary" @click="placeAnother">Place Another Order</button>
      </div>

      <!-- Budget section -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>

        <div class="budget-slider-row">
          <label class="slider-label" for="budget-slider">$0</label>
          <input
            id="budget-slider"
            type="range"
            class="budget-slider"
            min="0"
            max="500000"
            step="5000"
            v-model.number="budget"
          />
          <label class="slider-label" for="budget-slider">$500,000</label>
        </div>

        <div class="budget-rows">
          <div class="budget-row">
            <span class="budget-label">Budget</span>
            <span class="budget-value budget-value--bold">{{ formatCurrency(budget) }}</span>
          </div>
          <div class="budget-row">
            <span class="budget-label">Selected Cost</span>
            <span
              class="budget-value budget-value--bold"
              :class="overBudget ? 'budget-value--over' : 'budget-value--under'"
            >{{ formatCurrency(totalCost) }}</span>
          </div>
        </div>

        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{
              width: budgetPercent + '%',
              background: overBudget ? '#dc2626' : '#2563eb'
            }"
          ></div>
        </div>
        <div v-if="overBudget" class="over-budget-hint">
          Selected items exceed available budget by {{ formatCurrency(totalCost - budget) }}.
        </div>
      </div>

      <!-- Recommendations section -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items</h3>
          <span class="card-subtitle">Low stock items with increasing demand trend</span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No restocking recommendations at this time.
        </div>

        <div v-else>
          <div class="table-container">
            <table class="restock-table">
              <thead>
                <tr>
                  <th class="col-check"></th>
                  <th class="col-sku">SKU</th>
                  <th class="col-name">Item Name</th>
                  <th class="col-stock">Current Stock / Reorder Point</th>
                  <th class="col-qty">Forecast Qty</th>
                  <th class="col-unit">Unit Cost</th>
                  <th class="col-total">Total Cost</th>
                  <th class="col-trend">Trend</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in recommendations"
                  :key="item.sku"
                  :class="{ 'row-deselected': !selectedSkus.has(item.sku) }"
                  @click="toggleItem(item.sku)"
                  class="restock-row"
                >
                  <td class="col-check">
                    <input
                      type="checkbox"
                      :checked="selectedSkus.has(item.sku)"
                      @click.stop="toggleItem(item.sku)"
                      class="item-checkbox"
                    />
                  </td>
                  <td class="col-sku">
                    <span class="badge badge--sku">{{ item.sku }}</span>
                  </td>
                  <td class="col-name">{{ item.name }}</td>
                  <td class="col-stock">
                    <span :class="item.current_stock < item.reorder_point ? 'stock-low' : 'stock-ok'">
                      {{ item.current_stock.toLocaleString() }}
                    </span>
                    <span class="stock-separator"> / </span>
                    <span class="stock-reorder">{{ item.reorder_point.toLocaleString() }}</span>
                  </td>
                  <td class="col-qty">{{ item.forecasted_demand.toLocaleString() }}</td>
                  <td class="col-unit">{{ formatCurrency(item.unit_cost) }}</td>
                  <td
                    class="col-total"
                    :class="{ 'cost-deselected': !selectedSkus.has(item.sku) }"
                  >
                    <strong>{{ formatCurrency(item.total_cost) }}</strong>
                  </td>
                  <td class="col-trend">
                    <span :class="['badge', item.trend]">{{ item.trend }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="table-footer">
            <span class="selection-count">
              {{ selectedItems.length }} of {{ recommendations.length }} items selected
            </span>
            <span
              class="total-label"
              :class="overBudget ? 'total-label--over' : ''"
            >
              Total: <strong>{{ formatCurrency(totalCost) }}</strong>
            </span>
          </div>
        </div>
      </div>

      <!-- Place Order -->
      <div class="order-actions">
        <button
          class="btn-primary"
          :class="{ 'btn-primary--disabled': selectedItems.length === 0 || overBudget || submitting }"
          :disabled="selectedItems.length === 0 || overBudget || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Placing...' : 'Place Order' }}
        </button>
        <span v-if="overBudget" class="action-hint action-hint--error">
          Reduce selection or increase budget to place order.
        </span>
        <span v-else-if="selectedItems.length === 0" class="action-hint">
          Select at least one item to place an order.
        </span>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(100000)
    const recommendations = ref([])
    // Vue does not track internal Set mutations (add/delete), so after any mutation
    // we reassign with `new Set(...)` to create a new reference and trigger reactivity.
    const selectedSkus = ref(new Set())
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submittedOrder = ref(null)

    const selectedItems = computed(() =>
      recommendations.value.filter(r => selectedSkus.value.has(r.sku))
    )

    const totalCost = computed(() =>
      selectedItems.value.reduce((sum, r) => sum + r.total_cost, 0)
    )

    const overBudget = computed(() => totalCost.value > budget.value)

    const budgetPercent = computed(() => {
      if (budget.value === 0) return 100
      return Math.min((totalCost.value / budget.value) * 100, 100)
    })

    const formatCurrency = (value) => {
      return `${currencySymbol.value}${value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })}`
    }

    const toggleItem = (sku) => {
      const next = new Set(selectedSkus.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      // Assign new Set instance so Vue detects the change
      selectedSkus.value = next
    }

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations()
        recommendations.value = data
        // Default: select all items
        selectedSkus.value = new Set(data.map(r => r.sku))
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
        console.error('Restocking load error:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0 || overBudget.value || submitting.value) return
      try {
        submitting.value = true
        const result = await api.createRestockingOrder({ items: selectedItems.value })
        submittedOrder.value = result
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
        console.error('Restocking order error:', err)
      } finally {
        submitting.value = false
      }
    }

    const placeAnother = () => {
      submittedOrder.value = null
      // Re-select all items
      selectedSkus.value = new Set(recommendations.value.map(r => r.sku))
    }

    onMounted(loadRecommendations)

    return {
      budget,
      recommendations,
      selectedSkus,
      loading,
      error,
      submitting,
      submittedOrder,
      selectedItems,
      totalCost,
      overBudget,
      budgetPercent,
      currencySymbol,
      formatCurrency,
      toggleItem,
      placeOrder,
      placeAnother
    }
  }
}
</script>

<style scoped>
.restocking {
  /* Page wrapper — inherits padding from .main-content */
}

/* Success banner */
.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  color: #065f46;
  font-size: 0.938rem;
}

.success-banner-text {
  flex: 1;
}

/* Budget slider */
.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  height: 4px;
  accent-color: #2563eb;
  cursor: pointer;
}

/* Budget summary rows */
.budget-rows {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.875rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.938rem;
}

.budget-label {
  color: #64748b;
}

.budget-value {
  color: #0f172a;
}

.budget-value--bold {
  font-weight: 700;
}

.budget-value--over {
  color: #dc2626;
}

.budget-value--under {
  color: #059669;
}

/* Progress bar */
.progress-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease, background 0.2s ease;
}

.over-budget-hint {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #dc2626;
}

/* Card subtitle */
.card-subtitle {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 400;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Restock table */
.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-check  { width: 40px; }
.col-sku    { width: 130px; }
.col-name   { width: auto; }
.col-stock  { width: 200px; }
.col-qty    { width: 110px; }
.col-unit   { width: 110px; }
.col-total  { width: 120px; }
.col-trend  { width: 110px; }

.restock-row {
  cursor: pointer;
}

.restock-row.row-deselected {
  opacity: 0.5;
}

.item-checkbox {
  cursor: pointer;
  width: 15px;
  height: 15px;
  accent-color: #2563eb;
}

/* SKU badge override — small gray pill */
.badge--sku {
  background: #f1f5f9;
  color: #475569;
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  text-transform: none;
  letter-spacing: 0;
  font-family: 'Courier New', Courier, monospace;
}

.stock-low {
  color: #dc2626;
  font-weight: 600;
}

.stock-ok {
  color: #059669;
  font-weight: 600;
}

.stock-separator {
  color: #94a3b8;
}

.stock-reorder {
  color: #64748b;
}

.cost-deselected {
  color: #94a3b8;
}

/* Table footer */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.875rem;
  padding-top: 0.875rem;
  border-top: 1px solid #e2e8f0;
  font-size: 0.875rem;
  color: #64748b;
}

.total-label {
  font-size: 0.938rem;
  color: #0f172a;
}

.total-label--over {
  color: #dc2626;
}

/* Order actions */
.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
  margin-bottom: 1.5rem;
}

/* Buttons */
.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary--disabled,
.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
  white-space: nowrap;
}

.btn-secondary:hover {
  background: #eff6ff;
}

.action-hint {
  font-size: 0.813rem;
  color: #64748b;
}

.action-hint--error {
  color: #dc2626;
}
</style>
