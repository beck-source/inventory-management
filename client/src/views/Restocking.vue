<template>
  <div class="restocking">
    <div class="page-header">
      <h2 class="page-title">{{ t('restocking.title') }}</h2>
      <p class="page-description">{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-row">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budgetSlider') }}</label>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          class="budget-slider"
        />
        <div class="budget-scale">
          <span>{{ money(BUDGET_MIN) }}</span>
          <span>{{ money(BUDGET_MAX) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value">{{ money(selectedTotal) }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(remaining) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.selectedItems') }}</div>
          <div class="stat-value">{{ selectedLines.length }}</div>
        </div>
      </div>

      <div v-if="successMessage" class="notice notice-success">{{ successMessage }}</div>
      <div v-if="submitError" class="notice notice-error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ rows.length }})</h3>
        </div>

        <div v-if="rows.length === 0" class="loading">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-check">{{ t('restocking.select') }}</th>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.name') }}</th>
                <th>{{ t('restocking.trend') }}</th>
                <th class="num">{{ t('restocking.unitCost') }}</th>
                <th class="num">{{ t('restocking.quantity') }}</th>
                <th class="num">{{ t('restocking.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku" :class="{ unselected: !selection[row.sku].checked }">
                <td class="col-check">
                  <input
                    v-model="selection[row.sku].checked"
                    type="checkbox"
                    :aria-label="t('restocking.select') + ' ' + row.sku"
                  />
                </td>
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                </td>
                <td class="num">{{ money(row.unitCost, 2) }}</td>
                <td class="num">
                  <input
                    v-model.number="selection[row.sku].quantity"
                    type="number"
                    min="1"
                    step="1"
                    class="qty-input"
                    @blur="normalizeQuantity(row.sku)"
                  />
                </td>
                <td class="num"><strong>{{ money(lineCost(row)) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="order-footer">
          <div v-if="overBudget" class="over-budget">{{ t('restocking.overBudget') }}</div>
          <button class="place-order" :disabled="!canSubmit" @click="placeOrder">
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_MIN = 0
const BUDGET_MAX = 50000
const BUDGET_STEP = 500

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(20000)
    const selection = reactive({})
    const submitting = ref(false)
    const successMessage = ref('')
    const submitError = ref('')

    // Data is USD; convert only for display
    const money = (usd, decimals = 0) => {
      const value = Number(usd) || 0
      return formatCurrencyWithDecimals(value, currentCurrency.value, decimals)
    }

    // Items with positive forecast gap, largest gap first
    const rows = computed(() => {
      return forecasts.value
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          category: f.category,
          trend: f.trend,
          unitCost: Number(f.unit_cost) || 0,
          gap: (Number(f.forecasted_demand) || 0) - (Number(f.current_demand) || 0)
        }))
        .filter(r => r.gap > 0 && r.unitCost > 0)
        .sort((a, b) => b.gap - a.gap)
    })

    // Reset selection to greedy recommendation for the current budget
    const applyRecommendation = () => {
      let left = budget.value
      for (const row of rows.value) {
        const cost = row.gap * row.unitCost
        const fits = cost <= left
        if (fits) left -= cost
        selection[row.sku] = { checked: fits, quantity: row.gap }
      }
    }

    const lineCost = (row) => {
      const sel = selection[row.sku]
      const qty = sel && Number(sel.quantity) > 0 ? Number(sel.quantity) : 0
      return qty * row.unitCost
    }

    const selectedLines = computed(() => {
      return rows.value
        .filter(r => selection[r.sku] && selection[r.sku].checked && Number(selection[r.sku].quantity) > 0)
        .map(r => ({
          sku: r.sku,
          name: r.name,
          category: r.category,
          quantity: Math.floor(Number(selection[r.sku].quantity)),
          unit_cost: r.unitCost
        }))
    })

    const selectedTotal = computed(() => {
      return selectedLines.value.reduce((sum, l) => sum + l.quantity * l.unit_cost, 0)
    })
    const remaining = computed(() => budget.value - selectedTotal.value)
    const overBudget = computed(() => selectedTotal.value > budget.value)
    const canSubmit = computed(() =>
      !submitting.value && selectedLines.value.length > 0 && !overBudget.value
    )

    const normalizeQuantity = (sku) => {
      const sel = selection[sku]
      const q = Math.floor(Number(sel.quantity))
      sel.quantity = Number.isFinite(q) && q >= 1 ? q : 1
    }

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        applyRecommendation()
      } catch (err) {
        error.value = t('restocking.failedLoad') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Moving the slider resets edits to the new recommendation
    watch(budget, () => {
      applyRecommendation()
    })

    const placeOrder = async () => {
      if (!canSubmit.value) return
      submitting.value = true
      successMessage.value = ''
      submitError.value = ''
      try {
        const order = await api.submitRestockOrder({
          budget: budget.value,
          items: selectedLines.value
        })
        successMessage.value = t('restocking.success', {
          orderNumber: order.order_number,
          days: order.lead_time_days
        })
        // Reset selection after success
        for (const row of rows.value) {
          selection[row.sku] = { checked: false, quantity: row.gap }
        }
      } catch (err) {
        const detail = err.response && err.response.data && err.response.data.detail
        submitError.value = typeof detail === 'string' ? detail : t('restocking.failedSubmit')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      loading,
      error,
      budget,
      selection,
      rows,
      selectedLines,
      selectedTotal,
      remaining,
      overBudget,
      canSubmit,
      submitting,
      successMessage,
      submitError,
      money,
      lineCost,
      normalizeQuantity,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.budget-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.budget-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  width: 100%;
  accent-color: var(--color-primary);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stats-grid .stat-card {
  box-shadow: var(--shadow-sm);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-6);
  min-width: 0;
}

.stats-grid .stat-label {
  font-size: var(--text-xs);
}

.stats-grid .stat-value {
  font-size: var(--text-2xl);
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-check {
  width: 72px;
  text-align: center;
}

.col-check input {
  accent-color: var(--color-primary);
}

.unselected td {
  color: var(--color-text-muted);
}

.qty-input {
  width: 88px;
  height: 36px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font: inherit;
  font-size: var(--text-sm);
  text-align: right;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.qty-input:focus-visible,
.budget-slider:focus-visible,
.place-order:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.notice {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
}

.notice-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.notice-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.order-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.over-budget {
  color: var(--color-danger);
  font-size: var(--text-sm);
  font-weight: 500;
}

.place-order {
  height: 40px;
  padding: 0 var(--space-6);
  background: var(--color-primary);
  color: var(--color-surface);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.place-order:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.place-order:disabled {
  background: var(--color-border);
  border-color: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .col-check {
    width: 56px;
  }
}

@media (max-width: 480px) {
  .order-footer {
    justify-content: stretch;
  }

  .place-order {
    width: 100%;
  }
}
</style>
