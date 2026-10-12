<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your available budget and we'll recommend items to restock based on demand forecasts.</p>
    </div>

    <!-- Budget Slider Card -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Available Budget</h3>
      </div>
      <div class="budget-controls">
        <div class="budget-display">
          <span class="budget-prefix">$</span>
          <input
            type="number"
            v-model.number="budget"
            class="budget-input"
            :min="1000"
            :max="100000"
            step="500"
            @blur="clampBudget"
          />
        </div>
        <div class="slider-wrapper">
          <span class="slider-label">$1K</span>
          <input
            type="range"
            v-model.number="budget"
            class="budget-slider"
            min="1000"
            max="100000"
            step="500"
          />
          <span class="slider-label">$100K</span>
        </div>
      </div>

      <!-- Budget summary bar -->
      <div class="budget-summary">
        <div class="budget-stat">
          <span class="bs-label">Budget</span>
          <span class="bs-value">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="budget-stat used">
          <span class="bs-label">Selected Cost</span>
          <span class="bs-value">${{ selectedCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
        </div>
        <div class="budget-stat" :class="remaining >= 0 ? 'remaining' : 'over'">
          <span class="bs-label">Remaining</span>
          <span class="bs-value">${{ Math.abs(remaining).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}{{ remaining < 0 ? ' over' : '' }}</span>
        </div>
        <div class="budget-stat">
          <span class="bs-label">Items Selected</span>
          <span class="bs-value">{{ selectedItems.length }}</span>
        </div>
      </div>

      <!-- Budget fill bar -->
      <div class="budget-bar-track">
        <div
          class="budget-bar-fill"
          :class="{ over: selectedCost > budget }"
          :style="{ width: Math.min(100, (selectedCost / budget) * 100) + '%' }"
        ></div>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Recommendations Table -->
    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
        <div class="card-actions">
          <button class="btn-secondary" @click="deselectAll">Deselect All</button>
          <button class="btn-secondary" @click="autoSelect">Auto-Select Within Budget</button>
        </div>
      </div>

      <div class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-check"></th>
              <th class="col-item">Item</th>
              <th class="col-trend">Trend</th>
              <th class="col-num">Current Demand</th>
              <th class="col-num">Forecasted</th>
              <th class="col-num">Qty to Order</th>
              <th class="col-cost">Unit Cost</th>
              <th class="col-cost">Total Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in recommendations"
              :key="item.sku"
              :class="{ selected: isSelected(item.sku), disabled: !isSelected(item.sku) && !canAfford(item) }"
              @click="toggleItem(item)"
            >
              <td class="col-check">
                <input
                  type="checkbox"
                  :checked="isSelected(item.sku)"
                  @click.stop="toggleItem(item)"
                  :disabled="!isSelected(item.sku) && !canAfford(item)"
                />
              </td>
              <td class="col-item">
                <div class="item-name">{{ item.name }}</div>
                <div class="item-sku">{{ item.sku }}</div>
              </td>
              <td class="col-trend">
                <span :class="['badge', trendClass(item.trend)]">{{ item.trend }}</span>
              </td>
              <td class="col-num">{{ item.current_demand.toLocaleString() }}</td>
              <td class="col-num forecast">{{ item.forecasted_demand.toLocaleString() }}</td>
              <td class="col-num">
                <input
                  type="number"
                  class="qty-input"
                  :value="getQty(item.sku, item.recommended_qty)"
                  @input="setQty(item.sku, $event.target.value)"
                  @click.stop
                  min="1"
                />
              </td>
              <td class="col-cost">${{ item.unit_cost.toFixed(2) }}</td>
              <td class="col-cost total">
                ${{ (item.unit_cost * getQty(item.sku, item.recommended_qty)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Place Order -->
    <div class="order-footer" v-if="!loading && !error">
      <div class="order-summary">
        <span v-if="selectedItems.length === 0" class="no-items">Select items above to place an order.</span>
        <span v-else>
          <strong>{{ selectedItems.length }}</strong> item{{ selectedItems.length !== 1 ? 's' : '' }} selected &nbsp;·&nbsp;
          Total: <strong>${{ selectedCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong> &nbsp;·&nbsp;
          Delivery in <strong>7 days</strong>
        </span>
      </div>
      <button
        class="btn-primary place-order-btn"
        :disabled="selectedItems.length === 0 || placing"
        @click="placeOrder"
      >
        {{ placing ? 'Submitting...' : 'Place Order' }}
      </button>
    </div>

    <!-- Success Toast -->
    <transition name="toast">
      <div v-if="successMsg" class="toast-success">
        {{ successMsg }}
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(25000)
    const recommendations = ref([])
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const successMsg = ref('')

    // Map of sku → selected (boolean)
    const selectedSkus = ref(new Set())

    // Map of sku → quantity override
    const qtyOverrides = ref({})

    const getQty = (sku, defaultQty) => {
      return qtyOverrides.value[sku] !== undefined ? qtyOverrides.value[sku] : defaultQty
    }

    const setQty = (sku, val) => {
      const n = Math.max(1, parseInt(val) || 1)
      qtyOverrides.value = { ...qtyOverrides.value, [sku]: n }
    }

    const isSelected = (sku) => selectedSkus.value.has(sku)

    const itemCost = (item) => item.unit_cost * getQty(item.sku, item.recommended_qty)

    // Total cost of all selected items
    const selectedCost = computed(() => {
      return recommendations.value
        .filter(i => selectedSkus.value.has(i.sku))
        .reduce((sum, i) => sum + itemCost(i), 0)
    })

    const remaining = computed(() => budget.value - selectedCost.value)

    const selectedItems = computed(() =>
      recommendations.value.filter(i => selectedSkus.value.has(i.sku))
    )

    // Whether an unselected item can be added within budget
    const canAfford = (item) => remaining.value >= itemCost(item)

    const toggleItem = (item) => {
      const next = new Set(selectedSkus.value)
      if (next.has(item.sku)) {
        next.delete(item.sku)
      } else if (canAfford(item)) {
        next.add(item.sku)
      }
      selectedSkus.value = next
    }

    // Greedily select items within budget, sorted by forecasted demand desc (already sorted by backend)
    const autoSelect = () => {
      const next = new Set()
      let spent = 0
      for (const item of recommendations.value) {
        const cost = itemCost(item)
        if (spent + cost <= budget.value) {
          next.add(item.sku)
          spent += cost
        }
      }
      selectedSkus.value = next
    }

    const deselectAll = () => {
      selectedSkus.value = new Set()
    }

    const clampBudget = () => {
      budget.value = Math.min(100000, Math.max(1000, budget.value || 1000))
    }

    // Re-run auto-select whenever budget changes (deselect items that no longer fit)
    watch(budget, () => {
      // Only trim selections that now exceed budget — don't re-add automatically
      const next = new Set()
      let spent = 0
      for (const sku of selectedSkus.value) {
        const item = recommendations.value.find(i => i.sku === sku)
        if (!item) continue
        const cost = itemCost(item)
        if (spent + cost <= budget.value) {
          next.add(sku)
          spent += cost
        }
      }
      selectedSkus.value = next
    })

    const trendClass = (trend) => {
      if (trend === 'increasing') return 'success'
      if (trend === 'decreasing') return 'danger'
      return 'warning'
    }

    const loadRecommendations = async () => {
      try {
        loading.value = true
        recommendations.value = await api.getRestockingRecommendations()
        // Auto-select on first load
        autoSelect()
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return
      placing.value = true
      try {
        const items = selectedItems.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: getQty(item.sku, item.recommended_qty),
          unit_cost: item.unit_cost,
          total_cost: itemCost(item),
          trend: item.trend,
          forecasted_demand: item.forecasted_demand
        }))
        await api.submitRestockingOrder({
          items,
          total_value: selectedCost.value,
          notes: 'Submitted from Restocking Planner'
        })
        successMsg.value = `Order placed for ${items.length} item${items.length !== 1 ? 's' : ''} — delivery in 7 days. View it in the Orders tab.`
        deselectAll()
        setTimeout(() => { successMsg.value = '' }, 5000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      budget, recommendations, loading, error, placing, successMsg,
      selectedItems, selectedCost, remaining,
      isSelected, canAfford, toggleItem, autoSelect, deselectAll,
      clampBudget, trendClass, getQty, setQty, placeOrder
    }
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
.page-header p  { color: #64748b; margin-top: 4px; font-size: 0.9rem; }

/* ── Budget Card ── */
.budget-card { margin-bottom: 20px; }

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0 16px;
}

.budget-display {
  display: flex;
  align-items: center;
  gap: 6px;
}
.budget-prefix { font-size: 1.4rem; font-weight: 700; color: #0f172a; }
.budget-input {
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
  border: none;
  border-bottom: 2px solid #e2e8f0;
  outline: none;
  width: 160px;
  padding: 4px 0;
  background: transparent;
}
.budget-input:focus { border-bottom-color: #3b82f6; }

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}
.slider-label { font-size: 12px; color: #94a3b8; min-width: 32px; }

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #3b82f6;
  cursor: pointer;
}

/* Summary row */
.budget-summary {
  display: flex;
  gap: 32px;
  padding: 16px 0 12px;
  border-top: 1px solid #e2e8f0;
  flex-wrap: wrap;
}
.budget-stat { display: flex; flex-direction: column; gap: 2px; }
.bs-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: #94a3b8; }
.bs-value { font-size: 1.1rem; font-weight: 700; color: #0f172a; }
.used   .bs-value { color: #3b82f6; }
.remaining .bs-value { color: #22c55e; }
.over   .bs-value { color: #ef4444; }

/* Fill bar */
.budget-bar-track {
  height: 8px;
  background: #f1f5f9;
  border-radius: 99px;
  overflow: hidden;
  margin-top: 4px;
}
.budget-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  border-radius: 99px;
  transition: width 0.3s ease;
}
.budget-bar-fill.over { background: linear-gradient(90deg, #f97316, #ef4444); }

/* ── Table ── */
.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.card-actions { display: flex; gap: 8px; }

.restock-table { width: 100%; border-collapse: collapse; }
.restock-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: #64748b;
  padding: 10px 12px;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}
.restock-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
  font-size: 0.875rem;
}
.restock-table tr { cursor: pointer; transition: background .1s; }
.restock-table tr:hover { background: #f8fafc; }
.restock-table tr.selected { background: #eff6ff; }
.restock-table tr.selected:hover { background: #dbeafe; }
.restock-table tr.disabled { opacity: 0.45; cursor: not-allowed; }

.col-check { width: 36px; }
.col-item  { min-width: 180px; }
.col-trend { width: 110px; }
.col-num   { width: 120px; text-align: right; }
.col-cost  { width: 110px; text-align: right; }

.item-name { font-weight: 600; color: #0f172a; }
.item-sku  { font-size: 11px; color: #94a3b8; margin-top: 2px; }

.forecast  { font-weight: 700; color: #3b82f6; }
.total     { font-weight: 700; color: #0f172a; }

/* Inline qty input */
.qty-input {
  width: 70px;
  text-align: right;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.875rem;
  background: #fff;
  color: #0f172a;
}
.qty-input:focus { outline: none; border-color: #3b82f6; }

/* ── Footer ── */
.order-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
  padding: 20px 24px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  gap: 16px;
  flex-wrap: wrap;
}
.order-summary { font-size: 0.9rem; color: #475569; }
.no-items { color: #94a3b8; }

.btn-primary {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.place-order-btn { min-width: 140px; }

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
}
.btn-secondary:hover { background: #e2e8f0; }

/* ── Toast ── */
.toast-success {
  position: fixed;
  bottom: 32px;
  right: 32px;
  background: #0f172a;
  color: #fff;
  padding: 14px 22px;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,.2);
  max-width: 380px;
  z-index: 1000;
  border-left: 4px solid #22c55e;
}
.toast-enter-active, .toast-leave-active { transition: all .3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(16px); }
</style>
