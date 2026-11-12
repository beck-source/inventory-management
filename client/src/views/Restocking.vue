<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <div class="budget-readout">{{ formatCurrency(budget) }}</div>
        <input
          id="budget-slider"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          max="100000"
          step="1000"
          :disabled="submitting"
        />
        <div class="slider-scale">
          <span>{{ formatCurrency(0) }}</span>
          <span>{{ formatCurrency(100000) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(remaining) }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.daysValue', { count: longestLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="placedOrder" class="card panel panel-success">
        <h3 class="panel-title">{{ t('restocking.successTitle') }}</h3>
        <div class="panel-grid">
          <div>
            <div class="panel-label">{{ t('restocking.orderId') }}</div>
            <div class="panel-value">{{ placedOrder.id }}</div>
          </div>
          <div>
            <div class="panel-label">{{ t('restocking.expectedDelivery') }}</div>
            <div class="panel-value">{{ formatDate(placedOrder.expected_delivery) }}</div>
          </div>
        </div>
        <div class="panel-actions">
          <router-link to="/orders" class="link-btn">{{ t('restocking.viewOrders') }}</router-link>
        </div>
      </div>

      <div class="card">
        <div class="card-header header-row">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="openConfirm"
          >
            {{ t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="showConfirm" class="panel confirm-panel">
          <h3 class="panel-title">{{ t('restocking.confirmTitle') }}</h3>
          <div class="panel-grid">
            <div>
              <div class="panel-label">{{ t('restocking.total') }}</div>
              <div class="panel-value">{{ formatCurrency(totalCost) }}</div>
            </div>
            <div>
              <div class="panel-label">{{ t('restocking.itemCount') }}</div>
              <div class="panel-value">{{ recommendations.length }}</div>
            </div>
            <div>
              <div class="panel-label">{{ t('restocking.longestLeadTime') }}</div>
              <div class="panel-value">{{ t('restocking.daysValue', { count: longestLeadTime }) }}</div>
            </div>
            <div>
              <div class="panel-label">{{ t('restocking.estimatedDelivery') }}</div>
              <div class="panel-value">{{ estimatedDelivery }}</div>
            </div>
          </div>
          <div v-if="submitError" class="error submit-error">{{ submitError }}</div>
          <div class="panel-actions">
            <button type="button" class="btn btn-primary" :disabled="submitting" @click="confirmOrder">
              {{ submitting ? t('restocking.submitting') : t('restocking.confirm') }}
            </button>
            <button type="button" class="btn btn-secondary" :disabled="submitting" @click="cancelConfirm">
              {{ t('restocking.cancel') }}
            </button>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.gap') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ translateProductName(rec.item_name) }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
                <td class="num">{{ rec.gap.toLocaleString() }}</td>
                <td class="num">{{ rec.quantity.toLocaleString() }}</td>
                <td class="num">{{ formatCurrency(rec.unit_cost) }}</td>
                <td class="num"><strong>{{ formatCurrency(rec.line_total) }}</strong></td>
                <td class="num">{{ rec.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(25000)

    const showConfirm = ref(false)
    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    const formatCurrency = (value) => {
      const n = Number(value) || 0
      return `${currencySymbol.value}${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    }

    const localeTag = () => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US')

    const formatDate = (dateString) => {
      const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
      const d = new Date(isDateOnly ? `${dateString}T00:00:00` : dateString)
      if (isNaN(d.getTime())) return dateString || ''
      return d.toLocaleDateString(localeTag(), { year: 'numeric', month: 'short', day: 'numeric' })
    }

    // Priority fill: largest forecast gap first, partial quantity if the full line does not fit
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .filter(f => f.forecasted_demand > f.current_demand &&
          typeof f.unit_cost === 'number' && f.unit_cost > 0)
        .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
        .sort((a, b) => b.gap - a.gap)

      let left = budget.value
      const result = []
      for (const c of candidates) {
        let qty = 0
        if (c.gap * c.unit_cost <= left) {
          qty = c.gap
        } else {
          qty = Math.floor(left / c.unit_cost)
        }
        if (qty > 0) {
          const lineTotal = Math.round(qty * c.unit_cost * 100) / 100
          left -= lineTotal
          result.push({ ...c, quantity: qty, line_total: lineTotal })
        }
      }
      return result
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.line_total, 0)
    )
    const remaining = computed(() => Math.max(0, budget.value - totalCost.value))
    const longestLeadTime = computed(() =>
      recommendations.value.reduce((max, r) => Math.max(max, r.lead_time_days || 0), 0)
    )
    const estimatedDelivery = computed(() => {
      const d = new Date()
      d.setDate(d.getDate() + longestLeadTime.value)
      return d.toLocaleDateString(localeTag(), { year: 'numeric', month: 'short', day: 'numeric' })
    })

    // Plan changes invalidate an open confirmation
    watch([budget, recommendations], () => {
      if (showConfirm.value && !submitting.value) showConfirm.value = false
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = t('restocking.loadFailed') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    const openConfirm = () => {
      if (recommendations.value.length === 0) return
      submitError.value = null
      placedOrder.value = null
      showConfirm.value = true
    }

    const cancelConfirm = () => {
      showConfirm.value = false
      submitError.value = null
    }

    const confirmOrder = async () => {
      if (submitting.value) return
      submitting.value = true
      submitError.value = null
      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({ item_sku: r.item_sku, quantity: r.quantity }))
        })
        placedOrder.value = order
        showConfirm.value = false
      } catch (err) {
        submitError.value =
          err.response?.data?.detail
            ? (typeof err.response.data.detail === 'string'
              ? err.response.data.detail
              : JSON.stringify(err.response.data.detail))
            : `${t('restocking.submitFailed')}: ${err.message}`
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      recommendations,
      totalCost,
      remaining,
      longestLeadTime,
      estimatedDelivery,
      showConfirm,
      submitting,
      submitError,
      placedOrder,
      formatCurrency,
      formatDate,
      openConfirm,
      cancelConfirm,
      confirmOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
}

.budget-readout {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0.25rem 0 1rem;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid #fff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.35);
  cursor: pointer;
}

.budget-slider::-moz-range-track {
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid #fff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.35);
  cursor: pointer;
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.35);
}

.budget-slider:focus-visible::-moz-range-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.35);
}

.budget-slider:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.num {
  text-align: right;
}

.btn,
.link-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid transparent;
}

.btn-primary,
.link-btn {
  background: #2563eb;
  color: #fff;
}

.btn-primary:hover:not(:disabled),
.link-btn:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #fff;
  color: #0f172a;
  border-color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fafc;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:focus-visible,
.link-btn:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.panel {
  padding: 1.25rem 1.5rem;
}

.confirm-panel {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.panel-success {
  border-left: 4px solid #16a34a;
  margin-bottom: 1.5rem;
}

.panel-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 1rem;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}

.panel-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.panel-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
}

.panel-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.submit-error {
  margin-top: 1rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
