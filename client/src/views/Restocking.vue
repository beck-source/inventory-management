<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))
    const formatMoney = (value) => `${currencySymbol.value}${Number(value || 0).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`

    const BUDGET_MIN = 0
    const BUDGET_MAX = 100000
    const BUDGET_STEP = 500
    const DEBOUNCE_MS = 250

    const budget = ref(20000)
    const rows = ref([])
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const orderError = ref(null)
    const confirmation = ref(null)

    let debounceTimer = null
    let requestId = 0

    const loadRecommendations = async () => {
      const currentRequest = ++requestId
      loading.value = true
      error.value = null
      try {
        const response = await api.getRestockRecommendations(budget.value)
        if (currentRequest !== requestId) return
        // Keep the user's previous selection/qty per sku when it still exists
        const previous = new Map(rows.value.map(r => [r.sku, r]))
        rows.value = response.items.map(item => {
          const prev = previous.get(item.sku)
          if (!prev) return { ...item, selected: true, qty: item.quantity }
          const max = Math.max(1, item.shortfall)
          const prevQty = Number(prev.qty)
          const qty = prev.qty === '' || !Number.isFinite(prevQty)
            ? item.quantity
            : Math.min(Math.max(1, Math.floor(prevQty)), max)
          return { ...item, selected: prev.selected, qty }
        })
      } catch (err) {
        if (currentRequest !== requestId) return
        error.value = t('restocking.loadFailed')
        rows.value = []
        console.error('Load error:', err)
      } finally {
        if (currentRequest === requestId) loading.value = false
      }
    }

    watch(budget, () => {
      loading.value = true
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })

    onMounted(loadRecommendations)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    const normalizeQty = (row) => {
      const max = Math.max(1, row.shortfall)
      let value = Math.floor(Number(row.qty))
      if (!Number.isFinite(value) || value < 1) value = 1
      if (value > max) value = max
      row.qty = value
    }

    // Live clamp: only fix over-cap values; leave empty/partial input for validation
    const clampQtyInput = (row) => {
      if (row.qty === '' || row.qty === null) return
      const value = Number(row.qty)
      if (Number.isFinite(value) && value > row.shortfall) row.qty = Math.max(1, row.shortfall)
    }

    const isValidQty = (row) => {
      const qty = row.qty
      return typeof qty === 'number' && Number.isInteger(qty) && qty >= 1 && qty <= row.shortfall
    }

    const selectedRows = computed(() => rows.value.filter(r => r.selected))

    const invalidRows = computed(() => selectedRows.value.filter(r => !isValidQty(r)))

    const toCents = (value) => Math.round(Number(value) * 100)

    const lineCost = (row) => {
      const qty = Number(row.qty)
      return Number.isFinite(qty) && qty > 0 ? Math.round(qty * row.unit_cost * 100) / 100 : 0
    }

    const selectedTotalCents = computed(() =>
      selectedRows.value.reduce((sum, r) => sum + toCents(lineCost(r)), 0)
    )
    const selectedTotal = computed(() => selectedTotalCents.value / 100)
    const remaining = computed(() => (toCents(budget.value) - selectedTotalCents.value) / 100)
    const orderLeadTime = computed(() =>
      selectedRows.value.reduce((max, r) => Math.max(max, r.lead_time_days || 0), 0)
    )
    const overBudget = computed(() => selectedTotalCents.value > toCents(budget.value))
    const nothingSelected = computed(() => selectedRows.value.length === 0)
    const canPlaceOrder = computed(
      () =>
        !placing.value &&
        !loading.value &&
        !overBudget.value &&
        !nothingSelected.value &&
        invalidRows.value.length === 0
    )

    const trendLabel = (trend) => {
      const key = `trends.${trend}`
      const label = t(key)
      return label === key ? trend : label
    }

    const formatDate = (dateString) => {
      const m = typeof dateString === 'string' && /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString)
      const date = m
        ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
        : new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      placing.value = true
      orderError.value = null
      confirmation.value = null
      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: selectedRows.value.map(r => ({ sku: r.sku, quantity: Number(r.qty) }))
        })
        confirmation.value = order
        await loadRecommendations()
      } catch (err) {
        const detail = err?.response?.data?.detail
        if (Array.isArray(detail) && detail[0]?.msg) orderError.value = detail[0].msg
        else if (typeof detail === 'string') orderError.value = detail
        else orderError.value = t('restocking.orderFailed')
        console.error('Order error:', err)
      } finally {
        placing.value = false
      }
    }

    return {
      t,
      translateProductName,
      formatMoney,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      rows,
      loading,
      error,
      placing,
      orderError,
      confirmation,
      selectedTotal,
      remaining,
      orderLeadTime,
      overBudget,
      nothingSelected,
      invalidRows,
      canPlaceOrder,
      normalizeQty,
      clampQtyInput,
      lineCost,
      trendLabel,
      formatDate,
      placeOrder
    }
  }
}
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        <span class="budget-value">{{ formatMoney(budget) }}</span>
      </div>
      <input
        v-model.number="budget"
        type="range"
        class="budget-slider"
        :min="BUDGET_MIN"
        :max="BUDGET_MAX"
        :step="BUDGET_STEP"
        :aria-label="t('restocking.budget')"
      />
      <div class="slider-scale">
        <span>{{ formatMoney(BUDGET_MIN) }}</span>
        <span>{{ formatMoney(BUDGET_MAX) }}</span>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.summary.selectedTotal') }}</div>
        <div class="stat-value">{{ formatMoney(selectedTotal) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
        <div class="stat-value">{{ formatMoney(budget) }}</div>
      </div>
      <div :class="['stat-card', overBudget ? 'danger' : 'success']">
        <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
        <div class="stat-value">{{ formatMoney(remaining) }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">{{ t('restocking.summary.leadTime') }}</div>
        <div class="stat-value">{{ t('restocking.summary.days', { count: orderLeadTime }) }}</div>
      </div>
    </div>

    <div v-if="confirmation" class="confirmation" role="status">
      <span>
        {{ t('restocking.confirmation', {
          number: confirmation.order_number,
          date: formatDate(confirmation.expected_delivery)
        }) }}
      </span>
      <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ rows.length }})</h3>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="rows.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-check">{{ t('restocking.table.select') }}</th>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.name') }}</th>
              <th>{{ t('restocking.table.category') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th class="num">{{ t('restocking.table.stock') }}</th>
              <th class="num">{{ t('restocking.table.forecast') }}</th>
              <th class="num">{{ t('restocking.table.shortfall') }}</th>
              <th class="num">{{ t('restocking.table.quantity') }}</th>
              <th class="num">{{ t('restocking.table.unitCost') }}</th>
              <th class="num">{{ t('restocking.table.lineCost') }}</th>
              <th class="num">{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.sku" :class="{ deselected: !row.selected }">
              <td class="col-check">
                <input
                  v-model="row.selected"
                  type="checkbox"
                  :aria-label="`${t('restocking.table.select')} ${row.sku}`"
                />
              </td>
              <td><strong>{{ row.sku }}</strong></td>
              <td>{{ translateProductName(row.name) }}</td>
              <td>{{ row.category }}</td>
              <td>
                <span :class="['badge', row.trend]">{{ trendLabel(row.trend) }}</span>
              </td>
              <td class="num">{{ row.current_stock.toLocaleString() }}</td>
              <td class="num">{{ row.forecasted_demand.toLocaleString() }}</td>
              <td class="num">{{ row.shortfall.toLocaleString() }}</td>
              <td class="num">
                <input
                  v-model.number="row.qty"
                  type="number"
                  class="qty-input"
                  min="1"
                  :max="row.shortfall"
                  step="1"
                  :disabled="!row.selected"
                  :aria-label="`${t('restocking.table.quantity')} ${row.sku}`"
                  @input="clampQtyInput(row)"
                  @change="normalizeQty(row)"
                />
              </td>
              <td class="num">{{ formatMoney(row.unit_cost) }}</td>
              <td class="num"><strong>{{ formatMoney(lineCost(row)) }}</strong></td>
              <td class="num">{{ row.lead_time_days }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="order-actions">
      <div v-if="overBudget" class="error inline-error">{{ t('restocking.summary.overBudget') }}</div>
      <div v-else-if="!loading && !error && invalidRows.length > 0" class="error inline-error">
        {{ t('restocking.summary.invalidQty') }}
      </div>
      <div v-else-if="!loading && !error && nothingSelected" class="hint">
        {{ t('restocking.summary.nothingSelected') }}
      </div>
      <div v-if="orderError" class="error inline-error">{{ orderError }}</div>
      <button type="button" class="place-order" :disabled="!canPlaceOrder" @click="placeOrder">
        {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.budget-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
  cursor: pointer;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.restock-table {
  width: 100%;
}

.restock-table th.num,
.restock-table td.num {
  text-align: right;
}

.col-check {
  width: 64px;
  text-align: center;
}

tr.deselected td {
  color: #94a3b8;
}

.qty-input {
  width: 80px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: right;
  color: #0f172a;
}

.qty-input:disabled {
  background: #f1f5f9;
}

.confirmation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #166534;
}

.confirmation-link {
  color: #2563eb;
  font-weight: 500;
}

.empty-state,
.hint {
  padding: 1rem;
  text-align: center;
  color: #64748b;
}

.order-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}

.inline-error {
  padding: 0.5rem 0.75rem;
}

.place-order {
  padding: 0.625rem 1.5rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.place-order:hover:not(:disabled) {
  background: #1e293b;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
