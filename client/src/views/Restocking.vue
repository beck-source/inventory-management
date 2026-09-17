<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set your available budget and place optimized restock orders based on demand forecasts and stock criticality.</p>
    </div>

    <!-- Success state -->
    <div v-if="placedOrder" class="success-banner">
      <div class="success-icon">✓</div>
      <div>
        <strong>Order {{ placedOrder.order_number }} placed successfully.</strong>
        <span> Expected delivery in {{ placedOrder.estimated_delivery_days }} business days — visible in the Orders tab.</span>
      </div>
      <button class="dismiss-btn" @click="placedOrder = null">Dismiss</button>
    </div>

    <!-- Budget control -->
    <div class="card budget-card">
      <div class="budget-header">
        <div>
          <div class="card-title">Available Budget</div>
          <div class="budget-hint">Slide to adjust — recommendations update automatically.</div>
        </div>
        <div class="budget-display">${{ budget.toLocaleString() }}</div>
      </div>
      <div class="slider-row">
        <span class="slider-label">$1K</span>
        <input
          type="range"
          class="budget-slider"
          :min="1000"
          :max="200000"
          :step="1000"
          v-model.number="budget"
          @input="onBudgetChange"
        />
        <span class="slider-label">$200K</span>
      </div>
      <div v-if="result" class="budget-allocation">
        <div class="alloc-item">
          <span class="alloc-label">Allocated to recommendations</span>
          <span class="alloc-value spend">${{ result.total_cost.toLocaleString() }}</span>
        </div>
        <div class="alloc-item">
          <span class="alloc-label">Remaining</span>
          <span class="alloc-value remain">${{ result.remaining_budget.toLocaleString() }}</span>
        </div>
        <div class="alloc-bar">
          <div class="alloc-fill" :style="{ width: allocationPct + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Loading / empty -->
    <div v-if="loading" class="loading">Loading recommendations…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="result && result.recommendations.length === 0" class="empty-state">
      No items need restocking within this budget.
    </div>

    <!-- Recommendations table -->
    <div v-else-if="result" class="card">
      <div class="card-header">
        <h3 class="card-title">
          Recommended Items
          <span class="count-badge">{{ result.recommendations.length }}</span>
        </h3>
        <div class="header-actions">
          <label class="select-all-label">
            <input type="checkbox" :checked="allSelected" @change="toggleAll" />
            Select all
          </label>
          <button
            class="btn-primary"
            :disabled="selectedSkus.size === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? 'Placing…' : 'Place Order' }}
          </button>
        </div>
      </div>

      <div v-if="selectedSkus.size > 0" class="selection-summary">
        {{ selectedSkus.size }} item{{ selectedSkus.size > 1 ? 's' : '' }} selected
        &mdash; Total: <strong>${{ selectedTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th class="col-check"></th>
              <th>Item</th>
              <th>Category</th>
              <th class="col-num">Recommended Qty</th>
              <th class="col-num">Unit Cost</th>
              <th class="col-num">Total Cost</th>
              <th class="col-num">Priority Score</th>
              <th class="col-num">Est. Delivery</th>
              <th>Signals</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in result.recommendations" :key="item.sku" :class="{ selected: selectedSkus.has(item.sku) }">
              <td class="col-check">
                <input type="checkbox" :checked="selectedSkus.has(item.sku)" @change="toggleItem(item)" />
              </td>
              <td>
                <div class="item-name">{{ item.name }}</div>
                <div class="item-sku">{{ item.sku }}</div>
              </td>
              <td>{{ item.category }}</td>
              <td class="col-num">{{ item.quantity_recommended.toLocaleString() }}</td>
              <td class="col-num">${{ item.unit_cost.toFixed(2) }}</td>
              <td class="col-num"><strong>${{ item.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
              <td class="col-num">
                <span :class="['score-badge', scoreTier(item.combined_score)]">
                  {{ scoreTier(item.combined_score) }}
                </span>
              </td>
              <td class="col-num">{{ item.estimated_delivery_days }} days</td>
              <td>
                <div class="signals">
                  <span v-if="item.below_reorder_point" class="signal signal-warn">Low stock</span>
                  <span v-if="item.is_in_backlog" class="signal signal-danger">In backlog</span>
                  <span v-if="item.demand_gap > 0" class="signal signal-info">+{{ item.demand_gap }} demand gap</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-footer">
        <button
          class="btn-primary btn-large"
          :disabled="selectedSkus.size === 0 || placing"
          @click="placeOrder"
        >
          {{ placing ? 'Placing order…' : `Place Order (${selectedSkus.size} item${selectedSkus.size !== 1 ? 's' : ''})` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'

const budget = ref(25000)

export default {
  name: 'Restocking',
  setup() {
    const result = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const placing = ref(false)
    const placedOrder = ref(null)
    const selectedSkus = ref(new Set())

    let debounceTimer = null

    const fetchRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        result.value = await api.getRestockRecommendations(budget.value)
        // Auto-select all by default
        selectedSkus.value = new Set(result.value.recommendations.map(r => r.sku))
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const onBudgetChange = () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(fetchRecommendations, 350)
    }

    const toggleItem = (item) => {
      const next = new Set(selectedSkus.value)
      if (next.has(item.sku)) next.delete(item.sku)
      else next.add(item.sku)
      selectedSkus.value = next
    }

    const allSelected = computed(() => {
      if (!result.value || result.value.recommendations.length === 0) return false
      return result.value.recommendations.every(r => selectedSkus.value.has(r.sku))
    })

    const toggleAll = () => {
      if (allSelected.value) {
        selectedSkus.value = new Set()
      } else {
        selectedSkus.value = new Set(result.value.recommendations.map(r => r.sku))
      }
    }

    const selectedTotal = computed(() => {
      if (!result.value) return 0
      return result.value.recommendations
        .filter(r => selectedSkus.value.has(r.sku))
        .reduce((sum, r) => sum + r.total_cost, 0)
    })

    const allocationPct = computed(() => {
      if (!result.value || budget.value === 0) return 0
      return Math.min(100, (result.value.total_cost / budget.value) * 100)
    })

    const scoreTier = (score) => {
      if (score >= 0.6) return 'high'
      if (score >= 0.3) return 'medium'
      return 'low'
    }

    const placeOrder = async () => {
      if (!result.value || selectedSkus.value.size === 0) return
      placing.value = true
      error.value = null
      try {
        const items = result.value.recommendations
          .filter(r => selectedSkus.value.has(r.sku))
          .map(r => ({
            sku: r.sku,
            name: r.name,
            category: r.category,
            quantity: r.quantity_recommended,
            unit_cost: r.unit_cost,
          }))
        placedOrder.value = await api.placeRestockOrder(items, budget.value)
        // Refresh recommendations after order
        await fetchRecommendations()
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(fetchRecommendations)

    return {
      budget, result, loading, error, placing, placedOrder,
      selectedSkus, allSelected, selectedTotal, allocationPct,
      onBudgetChange, toggleItem, toggleAll, scoreTier, placeOrder,
    }
  }
}
</script>

<style scoped>
.restocking { display: flex; flex-direction: column; gap: 1.25rem; }

/* Success banner */
.success-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  color: #15803d;
  font-size: 0.875rem;
}
.success-icon {
  font-size: 1.25rem;
  font-weight: 700;
  flex-shrink: 0;
}
.dismiss-btn {
  margin-left: auto;
  background: none;
  border: 1px solid #86efac;
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  color: #15803d;
  cursor: pointer;
  font-size: 0.813rem;
  flex-shrink: 0;
}

/* Budget card */
.budget-card { margin-bottom: 0; }
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}
.budget-hint { font-size: 0.813rem; color: #64748b; margin-top: 2px; }
.budget-display {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.03em;
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.slider-label { font-size: 0.75rem; color: #94a3b8; flex-shrink: 0; }
.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}
.budget-allocation {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.alloc-item { display: flex; justify-content: space-between; font-size: 0.875rem; }
.alloc-label { color: #64748b; }
.alloc-value.spend { font-weight: 600; color: #0f172a; }
.alloc-value.remain { font-weight: 600; color: #059669; }
.alloc-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
}
.alloc-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 99px;
  transition: width 0.3s ease;
}

/* Selection summary */
.selection-summary {
  font-size: 0.875rem;
  color: #64748b;
  padding: 0.625rem 0;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 0.5rem;
}

/* Header actions */
.header-actions { display: flex; align-items: center; gap: 1rem; }
.select-all-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #475569;
  cursor: pointer;
}
.count-badge {
  display: inline-block;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 99px;
  padding: 0.125rem 0.625rem;
  margin-left: 0.5rem;
}

/* Buttons */
.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { background: #93c5fd; cursor: not-allowed; }
.btn-large { padding: 0.75rem 2rem; font-size: 0.938rem; }

/* Table rows */
tbody tr.selected { background: #eff6ff; }
tbody tr.selected:hover { background: #dbeafe; }

/* Column widths */
.col-check { width: 40px; text-align: center; }
.col-num { text-align: right; white-space: nowrap; }

/* Item cell */
.item-name { font-weight: 500; color: #0f172a; font-size: 0.875rem; }
.item-sku { font-size: 0.75rem; color: #94a3b8; font-family: monospace; }

/* Score badge */
.score-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.score-badge.high { background: #fecaca; color: #991b1b; }
.score-badge.medium { background: #fed7aa; color: #92400e; }
.score-badge.low { background: #e0e7ff; color: #3730a3; }

/* Signals */
.signals { display: flex; flex-wrap: wrap; gap: 4px; }
.signal {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
}
.signal-warn { background: #fef9c3; color: #854d0e; }
.signal-danger { background: #fecaca; color: #991b1b; }
.signal-info { background: #dbeafe; color: #1e40af; }

/* Table footer */
.table-footer {
  padding: 1rem 0 0;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}
</style>
