<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Plan a budget-constrained restock against the latest demand forecast.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="budget-panel">
        <div class="budget-controls">
          <label for="budget-slider" class="budget-label">Budget</label>
          <input
            id="budget-slider"
            type="range"
            min="1000"
            max="100000"
            step="500"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-value">{{ formatCurrency(budget) }}</div>
        </div>

        <div class="budget-summary">
          <div class="summary-stat">
            <div class="summary-label">Budget Set</div>
            <div class="summary-value">{{ formatCurrency(budget) }}</div>
          </div>
          <div class="summary-stat">
            <div class="summary-label">Total Cost</div>
            <div class="summary-value">{{ formatCurrency(totalCost) }}</div>
          </div>
          <div class="summary-stat">
            <div class="summary-label">Remaining</div>
            <div :class="['summary-value', { negative: remainingBudget < 0 }]">
              {{ formatCurrency(remainingBudget) }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="successMessage" class="banner banner-success">{{ successMessage }}</div>
      <div v-if="submitError" class="banner banner-error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Restock ({{ forecasts.length }})</h3>
        </div>
        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th class="num">Forecasted Demand</th>
                <th class="num">Unit Cost</th>
                <th class="num">Lead Time (days)</th>
                <th class="num">Quantity</th>
                <th class="num">Line Total</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in forecasts" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td class="num">{{ item.forecasted_demand }}</td>
                <td class="num">${{ formatNumber(item.unit_cost) }}</td>
                <td class="num">{{ item.lead_time_days }}</td>
                <td class="num">
                  <input
                    type="number"
                    min="0"
                    class="qty-input"
                    :value="quantities[item.item_sku] || 0"
                    @input="onQuantityInput(item.item_sku, $event.target.value)"
                  />
                </td>
                <td class="num">${{ formatNumber(lineTotal(item)) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="actions">
          <button
            class="btn-primary"
            :disabled="!canPlaceOrder || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Submitting...' : 'Place Order' }}
          </button>
          <div v-if="overBudget" class="hint hint-error">Over budget — reduce quantities to submit.</div>
          <div v-else-if="totalQuantity === 0" class="hint">Set at least one quantity above zero.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(25000)
    // Quantities keyed by SKU. Reactive object so per-row edits stay reactive.
    const quantities = reactive({})

    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)
    let successTimer = null

    // Greedy fill: sort by forecasted_demand desc, then assign demand up to the
    // remaining budget, truncating the last row that overflows.
    // Re-runs on every budget change — fine for a workshop demo; manual edits
    // are intentionally overwritten when the slider moves so the UX stays
    // predictable (slider = source of truth, user fine-tunes after).
    const runGreedyFill = () => {
      const sorted = [...forecasts.value].sort(
        (a, b) => b.forecasted_demand - a.forecasted_demand
      )
      let remaining = budget.value
      for (const item of sorted) {
        const desired = item.forecasted_demand
        const cost = desired * item.unit_cost
        let qty
        if (cost <= remaining) {
          qty = desired
        } else {
          qty = Math.floor(remaining / item.unit_cost)
          if (qty < 0) qty = 0
        }
        quantities[item.item_sku] = qty
        remaining -= qty * item.unit_cost
        if (remaining <= 0) remaining = 0
      }
    }

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getDemandForecasts()
        forecasts.value = data
        runGreedyFill()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const onQuantityInput = (sku, value) => {
      const n = parseInt(value, 10)
      quantities[sku] = Number.isFinite(n) && n >= 0 ? n : 0
    }

    const lineTotal = (item) => {
      const qty = quantities[item.item_sku] || 0
      return qty * item.unit_cost
    }

    const totalCost = computed(() =>
      forecasts.value.reduce((sum, item) => sum + lineTotal(item), 0)
    )

    const totalQuantity = computed(() =>
      forecasts.value.reduce((sum, item) => sum + (quantities[item.item_sku] || 0), 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)
    const overBudget = computed(() => totalCost.value > budget.value)

    const canPlaceOrder = computed(
      () => totalQuantity.value > 0 && !overBudget.value
    )

    // Re-run greedy auto-fill when budget changes. Workshop-grade simplicity:
    // we intentionally do NOT preserve user edits across slider moves.
    watch(budget, () => {
      runGreedyFill()
    })

    const placeOrder = async () => {
      // Re-entry guard: a single user gesture (programmatic .click(), double-tap,
      // or a stray duplicate event) must NEVER produce two POSTs. The button is
      // already :disabled while submitting, but disabled is only enforced on
      // pointer events — programmatic clicks via JS bypass it. This early-return
      // makes the handler idempotent regardless of how it was triggered.
      if (submitting.value) return
      submitError.value = null
      successMessage.value = null
      submitting.value = true
      try {
        const items = forecasts.value
          .filter((f) => (quantities[f.item_sku] || 0) > 0)
          .map((f) => ({
            sku: f.item_sku,
            name: f.item_name,
            quantity: quantities[f.item_sku],
            unit_price: f.unit_cost,
            lead_time_days: f.lead_time_days
          }))

        const order = await api.submitOrder({
          items,
          customer: 'Internal Restock'
        })

        successMessage.value = `Order ${order.order_number} submitted successfully.`
        // Reset quantities and re-run greedy fill at the current budget.
        for (const key of Object.keys(quantities)) delete quantities[key]
        runGreedyFill()

        if (successTimer) clearTimeout(successTimer)
        successTimer = setTimeout(() => {
          successMessage.value = null
        }, 5000)
      } catch (err) {
        submitError.value =
          'Failed to submit order: ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    const formatCurrency = (value) => {
      const sign = value < 0 ? '-' : ''
      return sign + '$' + Math.abs(Math.round(value)).toLocaleString()
    }

    const formatNumber = (value) => {
      return Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    onMounted(loadForecasts)

    return {
      loading,
      error,
      forecasts,
      budget,
      quantities,
      submitting,
      submitError,
      successMessage,
      totalCost,
      totalQuantity,
      remainingBudget,
      overBudget,
      canPlaceOrder,
      onQuantityInput,
      lineTotal,
      placeOrder,
      formatCurrency,
      formatNumber
    }
  }
}
</script>

<style scoped>
.budget-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  position: sticky;
  top: 0;
  z-index: 5;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #f1f5f9;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  min-width: 70px;
}

.budget-slider {
  flex: 1;
  accent-color: #1e293b;
  height: 6px;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 110px;
  text-align: right;
}

.budget-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.summary-stat {
  background: #f8fafc;
  border-radius: 8px;
  padding: 0.875rem 1rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
  margin-top: 0.25rem;
}

.summary-value.negative {
  color: #dc2626;
}

.banner {
  padding: 0.875rem 1.125rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-weight: 500;
  font-size: 0.9rem;
}

.banner-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.banner-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.restock-table {
  width: 100%;
}

.restock-table th.num,
.restock-table td.num {
  text-align: right;
}

.qty-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  text-align: right;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.qty-input:hover {
  border-color: #cbd5e1;
}

.qty-input:focus {
  outline: none;
  border-color: #1e293b;
  box-shadow: 0 0 0 3px rgba(30, 41, 59, 0.1);
}

.actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  border-top: 1px solid #f1f5f9;
}

.btn-primary {
  background: #0f172a;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.hint {
  font-size: 0.825rem;
  color: #64748b;
}

.hint-error {
  color: #dc2626;
}
</style>
