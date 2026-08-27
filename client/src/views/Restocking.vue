<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set a budget and get recommendations for which items to restock based on demand growth.</p>
    </div>

    <!-- Success banner -->
    <div v-if="successMessage" class="banner banner-success">
      {{ successMessage }}
    </div>

    <!-- Error banner -->
    <div v-if="submitError" class="banner banner-error">
      {{ submitError }}
    </div>

    <div v-if="loading" class="loading">Loading demand forecasts and inventory...</div>
    <div v-else-if="loadError" class="error">{{ loadError }}</div>
    <div v-else>

      <!-- Budget slider card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
          <span class="budget-amount">{{ formatCurrency(budget) }}</span>
        </div>

        <div class="slider-wrapper">
          <span class="slider-label">$10,000</span>
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            min="10000"
            max="500000"
            step="5000"
          />
          <span class="slider-label">$500,000</span>
        </div>

        <!-- Allocated / Remaining progress bar -->
        <div class="budget-bar-wrap">
          <div class="budget-bar">
            <!-- Blue "Allocated" segment; width capped at 100% -->
            <div
              class="budget-bar-allocated"
              :style="{ width: Math.min(allocatedPct, 100) + '%' }"
            ></div>
          </div>
          <div class="budget-bar-legend">
            <span class="legend-dot legend-allocated"></span>
            <span>Allocated {{ formatCurrency(totalAllocated) }}</span>
            <span class="legend-dot legend-remaining" style="margin-left:1rem"></span>
            <span>Remaining {{ formatCurrency(Math.max(budget - totalAllocated, 0)) }}</span>
          </div>
        </div>
      </div>

      <!-- Recommendations table card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommendations</h3>
          <span class="badge info">{{ eligibleForecasts.length }} items with positive growth</span>
        </div>

        <div v-if="eligibleForecasts.length === 0" class="empty-state">
          No items with positive demand growth found.
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Current Demand</th>
                <th>Forecasted Demand</th>
                <th>Growth %</th>
                <th>Qty to Restock</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, index) in eligibleForecasts"
                :key="item.sku"
                :class="{ 'row-selected': item.selected, 'row-over-budget': !item.selected }"
              >
                <!-- Order number = rank by growth descending -->
                <td class="col-num">{{ index + 1 }}</td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>{{ item.current_demand.toLocaleString() }}</td>
                <td><strong>{{ item.forecasted_demand.toLocaleString() }}</strong></td>
                <td>
                  <span class="growth-pct">+{{ item.growth_pct.toFixed(1) }}%</span>
                </td>
                <td>{{ item.restock_qty.toLocaleString() }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ formatCurrency(item.item_total_cost) }}</strong></td>
                <td>
                  <!-- Checkbox + status pill -->
                  <div class="status-cell">
                    <span class="checkbox" :class="{ checked: item.selected }">
                      <svg v-if="item.selected" viewBox="0 0 12 12" fill="none" class="check-icon">
                        <path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </span>
                    <span v-if="item.selected" class="badge success">Selected</span>
                    <span v-else class="badge danger">Over budget</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary bar + Place Order button -->
        <div class="order-footer">
          <div class="summary-bar">
            <strong>{{ selectedItems.length }} item{{ selectedItems.length !== 1 ? 's' : '' }} selected</strong>
            <span class="summary-sep">·</span>
            <span>Total: <strong>{{ formatCurrency(totalAllocated) }}</strong></span>
            <span class="summary-sep">·</span>
            <span>Budget remaining: <strong>{{ formatCurrency(Math.max(budget - totalAllocated, 0)) }}</strong></span>
          </div>

          <button
            class="btn-place-order"
            :disabled="selectedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Submitting...' : 'Place Restocking Order' }}
          </button>
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
    // ── Raw data ───────────────────────────────────────────────────────────────
    const forecasts    = ref([])   // from api.getDemandForecasts()
    const inventory    = ref([])   // from api.getInventory({})
    const loading      = ref(true)
    const loadError    = ref(null)

    // ── UI state ───────────────────────────────────────────────────────────────
    const budget       = ref(100000)   // default $100,000
    const submitting   = ref(false)
    const successMessage = ref('')
    const submitError  = ref('')

    // ── Helpers ────────────────────────────────────────────────────────────────
    const formatCurrency = (val) =>
      val.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

    // ── Data loading ───────────────────────────────────────────────────────────
    const loadData = async () => {
      loading.value  = true
      loadError.value = null
      try {
        // Fetch both in parallel; inventory loaded without filters so we get all unit_costs
        const [forecastData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = forecastData
        inventory.value = inventoryData
      } catch (err) {
        loadError.value = 'Failed to load data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // ── Join + algorithm ───────────────────────────────────────────────────────
    /**
     * eligibleForecasts: computed list of items ready for the table.
     *
     * Steps:
     *  1. Build a lookup map  sku → unit_cost  from inventory.
     *  2. Keep only forecasts where forecasted_demand > current_demand (positive growth).
     *  3. Compute growth_pct and restock_qty for each qualifying forecast.
     *  4. Sort descending by growth_pct (highest priority first).
     *  5. Greedy pass: walk the sorted list, accumulate running cost; mark an item
     *     "selected" if adding it does NOT exceed the budget, skip it otherwise.
     *     (Items that were skipped mid-list are still shown but flagged over-budget.)
     */
    const eligibleForecasts = computed(() => {
      // Step 1 – build sku → unit_cost map from inventory
      const costMap = {}
      for (const inv of inventory.value) {
        // Inventory items may appear multiple times (different warehouses); take first found.
        if (!(inv.sku in costMap)) {
          costMap[inv.sku] = inv.unit_cost ?? 0
        }
      }

      // Step 2 – filter to positive-growth forecasts and join unit_cost
      const candidates = []
      for (const fc of forecasts.value) {
        if (fc.forecasted_demand <= fc.current_demand) continue  // no growth, skip

        const unit_cost = costMap[fc.item_sku] ?? 0
        // Step 3 – compute derived fields
        const restock_qty     = fc.forecasted_demand - fc.current_demand
        // growth_pct = (forecasted - current) / current * 100
        const growth_pct      = (restock_qty / fc.current_demand) * 100
        const item_total_cost = restock_qty * unit_cost

        candidates.push({
          // Use item_sku as the unique key so v-for is stable
          sku:               fc.item_sku,
          name:              fc.item_name,
          current_demand:    fc.current_demand,
          forecasted_demand: fc.forecasted_demand,
          growth_pct,
          restock_qty,
          unit_cost,
          item_total_cost,
          selected: false   // will be set in greedy pass below
        })
      }

      // Step 4 – sort by growth_pct descending (highest growth = highest priority)
      candidates.sort((a, b) => b.growth_pct - a.growth_pct)

      // Step 5 – greedy selection: walk in priority order, select if within budget
      let running = 0
      for (const item of candidates) {
        if (running + item.item_total_cost <= budget.value) {
          item.selected = true
          running += item.item_total_cost
        }
        // Items that don't fit remain selected = false (shown as "Over budget")
      }

      return candidates
    })

    // Items that passed the greedy selection
    const selectedItems = computed(() =>
      eligibleForecasts.value.filter(i => i.selected)
    )

    // Total cost of selected items (drives progress bar and summary)
    const totalAllocated = computed(() =>
      selectedItems.value.reduce((sum, i) => sum + i.item_total_cost, 0)
    )

    // Percentage of budget consumed (used for progress bar width)
    const allocatedPct = computed(() =>
      budget.value > 0 ? (totalAllocated.value / budget.value) * 100 : 0
    )

    // ── Place order ────────────────────────────────────────────────────────────
    const placeOrder = async () => {
      if (selectedItems.value.length === 0 || submitting.value) return

      submitting.value  = true
      submitError.value = ''
      successMessage.value = ''

      // Build payload: each item maps to the shape the API expects
      const items = selectedItems.value.map(i => ({
        sku:        i.sku,
        name:       i.name,
        quantity:   i.restock_qty,
        unit_cost:  i.unit_cost,
        total_cost: i.item_total_cost
      }))

      try {
        const result = await api.createRestockingOrder({
          items,
          total_cost: totalAllocated.value,
          budget:     budget.value
        })

        // Format success message from API response fields
        const orderId   = result.order_id ?? result.id ?? 'RST-ORDER'
        const delivery  = result.expected_delivery
          ? new Date(result.expected_delivery).toLocaleDateString('en-US', {
              year: 'numeric', month: 'long', day: 'numeric'
            })
          : 'TBD'

        successMessage.value =
          `Restocking order ${orderId} submitted. Expected delivery: ${delivery}`

        // Scroll to top so user sees the banner
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } catch (err) {
        submitError.value = 'Failed to submit order: ' + (err.response?.data?.detail ?? err.message)
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      loadError,
      budget,
      eligibleForecasts,
      selectedItems,
      totalAllocated,
      allocatedPct,
      submitting,
      successMessage,
      submitError,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* ── Page layout ──────────────────────────────────────────────────────────── */
.restocking {
  padding-bottom: 2rem;
}

/* ── Banners ──────────────────────────────────────────────────────────────── */
.banner {
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.banner-success {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
}

.banner-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

/* ── Budget card ──────────────────────────────────────────────────────────── */
.budget-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
  flex-shrink: 0;
}

.budget-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
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
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37,99,235,0.4);
  transition: box-shadow 0.15s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 2px 8px rgba(37,99,235,0.5);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37,99,235,0.4);
}

/* ── Budget progress bar ──────────────────────────────────────────────────── */
.budget-bar-wrap {
  margin-top: 0.25rem;
}

.budget-bar {
  height: 10px;
  background: #e2e8f0;   /* light gray = "Remaining" */
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.budget-bar-allocated {
  height: 100%;
  background: #2563eb;   /* blue = "Allocated" */
  border-radius: 5px;
  transition: width 0.3s ease;
  min-width: 0;
}

.budget-bar-legend {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.813rem;
  color: #64748b;
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-allocated  { background: #2563eb; }
.legend-remaining  { background: #e2e8f0; border: 1px solid #cbd5e1; }

/* ── Table row states ─────────────────────────────────────────────────────── */
.row-selected {
  background: #eff6ff !important;  /* blue tint for selected rows */
}

.row-over-budget {
  opacity: 0.55;   /* dim over-budget rows */
}

/* ── Growth percentage ────────────────────────────────────────────────────── */
.growth-pct {
  font-weight: 600;
  color: #059669;
}

/* ── Status cell (checkbox + badge) ──────────────────────────────────────── */
.status-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid #cbd5e1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #fff;
  transition: background 0.15s, border-color 0.15s;
}

.checkbox.checked {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.check-icon {
  width: 12px;
  height: 12px;
}

/* ── Order footer (summary + button) ─────────────────────────────────────── */
.order-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.summary-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.938rem;
  color: #334155;
  flex-wrap: wrap;
}

.summary-sep {
  color: #cbd5e1;
}

.btn-place-order {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  white-space: nowrap;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ── Empty state ──────────────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* ── Column widths ────────────────────────────────────────────────────────── */
.col-num {
  color: #94a3b8;
  font-size: 0.813rem;
  width: 36px;
}
</style>
