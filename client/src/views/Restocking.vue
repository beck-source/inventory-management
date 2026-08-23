<template>
  <div class="restocking-view">

    <!-- Page header -->
    <div class="page-header">
      <h2>Restocking</h2>
      <p class="page-description">Allocate budget to restock items based on demand forecasts.</p>
    </div>

    <!-- Loading / error -->
    <div v-if="loading" class="loading-state">Loading recommendations...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else>

      <!-- Budget card -->
      <div class="card budget-card">
        <div class="card-header">
          <div class="budget-header-left">
            <h3 class="card-title">Available Budget</h3>
            <button class="collapse-btn" @click="budgetExpanded = !budgetExpanded">
              {{ budgetExpanded ? '▲' : '▼' }}
            </button>
          </div>
          <span class="budget-value">${{ budget.toLocaleString() }}</span>
        </div>
        <input
          v-show="budgetExpanded"
          type="range"
          min="0"
          max="500000"
          step="1000"
          v-model.number="budget"
          class="budget-slider"
        />
        <div v-show="budgetExpanded" class="budget-range-labels">
          <span>$0</span>
          <span>$500,000</span>
        </div>
      </div>

      <!-- Recommendations card -->
      <div class="card recommendations-card">
        <div class="card-header">
          <h3 class="card-title">
            Restock Recommendations
            <span class="count-badge">{{ recommendations.length }}</span>
          </h3>
          <div class="order-actions">
            <span :class="['running-total', { 'over-budget': runningTotal > budget }]">
              ${{ runningTotal.toLocaleString() }} / ${{ budget.toLocaleString() }}
            </span>
            <button
              class="btn-primary"
              :disabled="!canPlaceOrder"
              @click="placeOrder"
            >
              {{ submitting ? 'Placing Order...' : `Place Order (${selectedItems.length} items)` }}
            </button>
          </div>
        </div>

        <!-- Success banner -->
        <div v-if="submitted" class="success-banner">
          Order {{ submittedOrderNumber }} placed successfully. Expected delivery in 14 days.
          <router-link to="/orders" class="success-link">View in Orders</router-link>
        </div>

        <!-- Empty state -->
        <div v-else-if="recommendations.length === 0" class="empty-state">
          No items with positive demand gap found.
        </div>

        <!-- Recommendations table -->
        <div v-else class="table-wrapper">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">SKU</th>
                <th class="col-name">Item Name</th>
                <th class="col-trend">Trend</th>
                <th class="col-qty">Recommended Qty</th>
                <th class="col-cost">Unit Cost</th>
                <th class="col-total">Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.id"
                :class="{ 'row-unchecked': !checkedState[item.id] }"
              >
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="checkedState[item.id]"
                    @change="toggleItem(item.id, $event.target.checked)"
                  />
                </td>
                <td class="col-sku">{{ item.item_sku }}</td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-trend">
                  <span :class="['trend-badge', `trend-${item.trend}`]">{{ item.trend }}</span>
                </td>
                <td class="col-qty">{{ item.recommended_quantity.toLocaleString() }}</td>
                <td class="col-cost">${{ item.unit_cost.toFixed(2) }}</td>
                <td class="col-total">${{ item.line_total.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'

// Trend sort order: increasing items come first (highest urgency), then stable, then decreasing
const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    // --- Reactive state ---
    const demandForecasts = ref([])
    // SKU string → inventory object lookup, built after loading inventory
    const inventoryMap = ref({})
    const budget = ref(250000)
    // Controls visibility of the slider; header always stays visible
    const budgetExpanded = ref(true)
    // Explicit checkbox toggles by the user: { [forecast.id]: boolean }
    const manualOverrides = ref({})
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitted = ref(false)
    const submittedOrderNumber = ref('')

    // --- Data loading ---
    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        // Fetch forecasts and full inventory in parallel
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        demandForecasts.value = forecastsData
        // Build a fast SKU → inventory object lookup to join on item_sku
        inventoryMap.value = Object.fromEntries(inventoryData.map(i => [i.sku, i]))
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => loadData())

    // Reset manual overrides whenever the budget slider moves so auto-selection
    // always re-derives a fresh greedy allocation from the new budget value.
    watch(budget, () => {
      manualOverrides.value = {}
    })

    // --- Computed properties ---

    // 1. Enrich forecasts with inventory data, filter to items with a positive
    //    demand gap and a known unit_cost, then sort by trend urgency then quantity.
    const recommendations = computed(() => {
      return demandForecasts.value
        .filter(fc => {
          const inv = inventoryMap.value[fc.item_sku]
          // Only include items present in inventory with a positive demand gap
          return inv && (fc.forecasted_demand - fc.current_demand) > 0
        })
        .map(fc => {
          const inv = inventoryMap.value[fc.item_sku]
          const recommended_quantity = fc.forecasted_demand - fc.current_demand
          const unit_cost = inv.unit_cost
          return {
            ...fc,
            unit_cost,
            warehouse: inv.warehouse,
            category: inv.category,
            recommended_quantity,
            line_total: recommended_quantity * unit_cost
          }
        })
        .sort((a, b) => {
          // Primary: trend urgency (increasing → stable → decreasing)
          const trendDiff = (TREND_ORDER[a.trend] ?? 99) - (TREND_ORDER[b.trend] ?? 99)
          if (trendDiff !== 0) return trendDiff
          // Secondary: larger quantity gap first within the same trend
          return b.recommended_quantity - a.recommended_quantity
        })
    })

    // 2. Greedy budget allocation: walk recommendations in sort order, mark each
    //    checked as long as the running spend stays within budget.
    const defaultChecked = computed(() => {
      let spent = 0
      const result = {}
      for (const item of recommendations.value) {
        if (spent + item.line_total <= budget.value) {
          result[item.id] = true
          spent += item.line_total
        } else {
          result[item.id] = false
        }
      }
      return result
    })

    // 3. Merge auto-allocation with user overrides (overrides win)
    const checkedState = computed(() => ({
      ...defaultChecked.value,
      ...manualOverrides.value
    }))

    // 4. Cost of currently selected items
    const runningTotal = computed(() =>
      recommendations.value
        .filter(item => checkedState.value[item.id])
        .reduce((sum, item) => sum + item.line_total, 0)
    )

    // 5. Items that are checked (to be included in the order)
    const selectedItems = computed(() =>
      recommendations.value.filter(item => checkedState.value[item.id])
    )

    // 6. Guard: need at least one item and no in-flight/completed submit
    const canPlaceOrder = computed(() =>
      selectedItems.value.length > 0 && !submitting.value && !submitted.value
    )

    // --- Methods ---

    // Record an explicit user toggle; this persists even when budget changes
    const toggleItem = (itemId, isChecked) => {
      manualOverrides.value[itemId] = isChecked
    }

    const placeOrder = async () => {
      submitting.value = true
      error.value = null
      try {
        const orderData = {
          items: selectedItems.value.map(item => ({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.recommended_quantity,
            unit_price: item.unit_cost
          }))
        }
        const result = await api.createRestockingOrder(orderData)
        submittedOrderNumber.value = result.order_number
        submitted.value = true
      } catch (err) {
        error.value = 'Failed to place restocking order: ' + err.message
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    return {
      budget,
      budgetExpanded,
      loading,
      error,
      submitting,
      submitted,
      submittedOrderNumber,
      recommendations,
      checkedState,
      runningTotal,
      selectedItems,
      canPlaceOrder,
      toggleItem,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* ---- Page header ---- */
.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px 0;
}

.page-description {
  color: #64748b;
  font-size: 0.9375rem;
  margin: 0;
}

/* ---- Loading / error ---- */
.loading-state {
  padding: 40px;
  text-align: center;
  color: #64748b;
}

.error-state {
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
}

/* ---- Card shell ---- */
.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

/* ---- Budget card ---- */
.budget-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
}

.collapse-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.budget-slider {
  width: 100%;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
  margin-bottom: 8px;
  display: block;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

/* ---- Recommendations card ---- */
.order-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.running-total {
  font-weight: 600;
  color: #16a34a;
  font-size: 0.9375rem;
}

.running-total.over-budget {
  color: #dc2626;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ---- Success banner ---- */
.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  padding: 12px 16px;
  color: #15803d;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.success-link:hover {
  text-decoration: underline;
}

/* ---- Empty state ---- */
.empty-state {
  text-align: center;
  color: #64748b;
  padding: 40px;
}

/* ---- Table ---- */
.table-wrapper {
  overflow-x: auto;
}

.recommendations-table {
  width: 100%;
  border-collapse: collapse;
}

.recommendations-table th,
.recommendations-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.recommendations-table th {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f8fafc;
}

.row-unchecked {
  opacity: 0.45;
}

/* Column widths */
.col-check  { width: 40px; }
.col-sku    { width: 100px; }
.col-name   { /* auto */ }
.col-trend  { width: 110px; }
.col-qty    { width: 150px; }
.col-cost   { width: 100px; }
.col-total  { width: 120px; }

/* ---- Count badge ---- */
.count-badge {
  background: #e2e8f0;
  color: #64748b;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 9999px;
  margin-left: 8px;
  font-weight: 500;
}

/* ---- Trend badges ---- */
.trend-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 9999px;
  text-transform: capitalize;
}

.trend-increasing {
  background: #dcfce7;
  color: #15803d;
}

.trend-stable {
  background: #f1f5f9;
  color: #64748b;
}

.trend-decreasing {
  background: #fee2e2;
  color: #dc2626;
}
</style>
