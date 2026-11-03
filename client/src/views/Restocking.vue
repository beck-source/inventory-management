<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="controls">
          <div class="control budget-control">
            <label for="budget-range" class="control-label">
              {{ t('restocking.budget') }}:
              <strong class="budget-readout">{{ formatCurrency(budget, currentCurrency) }}</strong>
            </label>
            <input
              id="budget-range"
              class="budget-range"
              type="range"
              min="0"
              :max="maxBudget"
              :step="step"
              :disabled="maxBudget <= 0"
              :style="{ '--fill': fillPercent + '%' }"
              v-model.number="budget"
            />
            <div class="range-scale">
              <span>{{ formatCurrency(0, currentCurrency) }}</span>
              <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
            </div>
          </div>
          <div class="control">
            <span class="control-label">{{ t('restocking.sortBy') }}</span>
            <div class="toggle" role="group">
              <button
                v-for="opt in sortOptions"
                :key="opt.value"
                type="button"
                :class="['toggle-btn', { active: sort === opt.value }]"
                :aria-pressed="sort === opt.value"
                @click="sort = opt.value"
              >{{ t(opt.label) }}</button>
            </div>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value">{{ formatCurrency(selectedTotal, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(remaining, currentCurrency) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.selectedItems') }}</div>
          <div class="stat-value">{{ selectedRows.length }}</div>
        </div>
      </div>

      <div v-if="overBudget" class="warning-box">
        {{ t('restocking.overBudget', { amount: formatCurrency(selectedTotal - budget, currentCurrency) }) }}
      </div>
      <div v-if="orderError" class="error">{{ orderError }}</div>
      <div v-if="placedOrder" class="success-box">
        {{ t('restocking.orderSuccess', { orderNumber: placedOrder.order_number, days: placedOrder.lead_time_days }) }}
        <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
      </div>

      <div class="card" :class="{ refreshing }">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ rows.length }})</h3>
          <button
            type="button"
            class="primary-btn"
            :disabled="!canSubmit"
            @click="placeOrder"
          >{{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}</button>
        </div>

        <div v-if="refreshError" class="error">{{ refreshError }}</div>
        <div v-if="rows.length === 0" class="empty">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-check">{{ t('restocking.table.select') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.stock') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in rows"
                :key="row.item_sku"
                :class="{ 'low-stock-row': row.is_low_stock }"
              >
                <td class="col-check">
                  <input type="checkbox" v-model="row.selected" :aria-label="row.item_name" />
                </td>
                <td><strong>{{ row.item_sku }}</strong></td>
                <td>
                  {{ translateProductName(row.item_name) }}
                  <span v-if="row.is_low_stock" class="badge danger low-badge">{{ t('restocking.lowStock') }}</span>
                </td>
                <td>
                  <span :class="['badge', row.trend]">{{ t('trends.' + row.trend) }}</span>
                </td>
                <td>{{ row.quantity_on_hand }} / {{ row.reorder_point }}</td>
                <td class="num">{{ formatCurrency(row.unit_cost, currentCurrency) }}</td>
                <td class="num">
                  <input
                    class="qty-input"
                    :class="{ invalid: !isValidQuantity(row) }"
                    type="number"
                    min="1"
                    :max="row.maxQuantity"
                    step="1"
                    :title="t('restocking.maxQuantity', { max: row.maxQuantity })"
                    v-model.number="row.quantity"
                    @change="normalizeQuantity(row)"
                  />
                </td>
                <td class="num">{{ formatCurrency(lineTotal(row), currentCurrency) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const refreshing = ref(false)
    const refreshError = ref(null)

    // All monetary values here are USD; formatCurrency converts for display only.
    const maxBudget = ref(0)
    const budget = ref(0)
    const sort = ref('demand_gap')
    const rows = ref([])

    const submitting = ref(false)
    const placedOrder = ref(null)
    const orderError = ref(null)

    const sortOptions = [
      { value: 'demand_gap', label: 'restocking.sortDemandGap' },
      { value: 'low_stock', label: 'restocking.sortLowStock' }
    ]

    // Roughly 100 slider positions, snapped to a "nice" step
    const step = computed(() => {
      const raw = maxBudget.value / 100
      if (raw <= 1) return 1
      const magnitude = Math.pow(10, Math.floor(Math.log10(raw)))
      return Math.max(1, Math.round(raw / magnitude) * magnitude)
    })

    // Drives the filled portion of the slider track
    const fillPercent = computed(() =>
      maxBudget.value > 0 ? Math.min(100, (budget.value / maxBudget.value) * 100) : 0
    )

    const toRows = (items) => items.map(item => ({
      ...item,
      selected: true,
      quantity: item.suggested_quantity,
      // Ordering more than the demand gap is not sensible
      maxQuantity: Math.max(item.demand_gap, item.suggested_quantity, 1)
    }))

    const isValidQuantity = (row) =>
      Number.isInteger(row.quantity) && row.quantity >= 1 && row.quantity <= row.maxQuantity

    // Clamp on commit (change event) so typing is not interrupted mid-edit
    const normalizeQuantity = (row) => {
      const n = Math.round(Number(row.quantity))
      if (!Number.isFinite(n) || row.quantity === '') {
        row.quantity = 1
        return
      }
      row.quantity = Math.min(row.maxQuantity, Math.max(1, n))
    }

    const lineTotal = (row) => (isValidQuantity(row) ? row.quantity * row.unit_cost : 0)

    // Only the latest request may apply its result (guards against out-of-order responses)
    let requestSeq = 0
    let debounceTimer = null

    const loadRecommendations = async (initial = false) => {
      const seq = ++requestSeq
      if (!initial) refreshing.value = true
      try {
        const data = await api.getRestockingRecommendations(budget.value, sort.value)
        if (seq !== requestSeq) return
        maxBudget.value = data.max_budget
        // Keep the slider value within the (possibly changed) range
        if (budget.value > data.max_budget) budget.value = data.max_budget
        rows.value = toRows(data.items)
        refreshError.value = null
      } catch (err) {
        if (seq !== requestSeq) return
        if (initial) throw err
        refreshError.value = t('restocking.loadFailed')
        console.error('Recommendation load error:', err)
      } finally {
        if (seq === requestSeq) refreshing.value = false
      }
    }

    const init = async () => {
      try {
        // Learn max_budget (cost of covering every gap) with a zero-budget request
        const seed = await api.getRestockingRecommendations(0, sort.value)
        maxBudget.value = seed.max_budget
        budget.value = Math.round((seed.max_budget * 0.25) / step.value) * step.value
        await loadRecommendations(true)
      } catch (err) {
        error.value = t('restocking.loadFailed') + ': ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // Debounced reload on slider / sort change (ignored until initial load completes)
    watch([budget, sort], () => {
      if (loading.value) return
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => loadRecommendations(false), DEBOUNCE_MS)
    })

    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestSeq++ // invalidate any in-flight request
    })

    const selectedRows = computed(() => rows.value.filter(r => r.selected))
    const selectedTotal = computed(() =>
      selectedRows.value.reduce((sum, r) => sum + lineTotal(r), 0)
    )
    const remaining = computed(() => budget.value - selectedTotal.value)
    const overBudget = computed(() => selectedTotal.value > budget.value + 1e-9)
    const canSubmit = computed(() =>
      !submitting.value &&
      selectedRows.value.length > 0 &&
      selectedRows.value.every(isValidQuantity)
    )

    const placeOrder = async () => {
      if (!canSubmit.value || submitting.value) return // double-submit guard
      submitting.value = true
      orderError.value = null
      placedOrder.value = null
      try {
        // Send only sku + quantity; the server prices the order itself
        const items = selectedRows.value.map(r => ({ sku: r.item_sku, quantity: r.quantity }))
        placedOrder.value = await api.createRestockingOrder(items)
      } catch (err) {
        const detail = err.response?.data?.detail
        orderError.value = typeof detail === 'string' ? detail : t('restocking.orderFailed')
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)

    return {
      t, currentCurrency, formatCurrency, translateProductName,
      loading, error, refreshing, refreshError,
      maxBudget, budget, sort, step, fillPercent, sortOptions,
      rows, isValidQuantity, normalizeQuantity, lineTotal,
      selectedRows, selectedTotal, remaining, overBudget, canSubmit,
      submitting, placedOrder, orderError, placeOrder
    }
  }
}
</script>

<style scoped>
.controls {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2rem;
  align-items: start;
}

.control {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-readout {
  color: #0f172a;
  font-size: 1rem;
  margin-left: 0.5rem;
}

/* Range slider: track fill driven by --fill */
.budget-range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #0f172a var(--fill, 0%), #e2e8f0 var(--fill, 0%));
  outline: none;
  cursor: pointer;
}

.budget-range:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.budget-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #0f172a;
}

.budget-range::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #0f172a;
}

.budget-range:focus-visible {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.35);
}

.range-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.toggle {
  display: inline-flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.toggle-btn {
  padding: 0.5rem 0.875rem;
  background: white;
  border: none;
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
}

.toggle-btn + .toggle-btn {
  border-left: 1px solid #e2e8f0;
}

.toggle-btn.active {
  background: #0f172a;
  color: white;
}

.primary-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn:hover:not(:disabled) {
  background: #1e293b;
}

.primary-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.warning-box,
.success-box {
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.warning-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

.success-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.success-box a {
  margin-left: 0.5rem;
  color: #166534;
  font-weight: 600;
  text-decoration: underline;
}

.refreshing {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #64748b;
}

.col-check {
  width: 64px;
}

.num {
  text-align: right;
}

.low-stock-row {
  background: #fef2f2;
}

.low-badge {
  margin-left: 0.5rem;
}

.qty-input {
  width: 80px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: right;
  font-size: 0.875rem;
  color: #0f172a;
}

.qty-input.invalid {
  border-color: #dc2626;
  background: #fef2f2;
}

@media (max-width: 800px) {
  .controls {
    grid-template-columns: 1fr;
  }
}
</style>
