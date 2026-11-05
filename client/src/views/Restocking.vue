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
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          max="500000"
          step="5000"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ money(0) }}</span>
          <span class="hint">{{ t('restocking.budgetHint') }}</span>
          <span>{{ money(500000) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.totalSpend') }}</div>
          <div class="stat-value">{{ money(totalSpend) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ money(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.itemCount') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: overallLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            class="place-order-btn"
            type="button"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="submitError" class="error">{{ submitError }}</div>
        <div v-if="placedOrder" class="success-message">
          {{ t('restocking.success', { orderNumber: placedOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ candidates.length === 0 ? t('restocking.emptyNoGap') : t('restocking.emptyNoBudget') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ rec.item_name }}</td>
                <td>{{ rec.category }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ trendLabel(rec.trend) }}</span>
                </td>
                <td class="num">{{ rec.on_hand.toLocaleString() }}</td>
                <td class="num">{{ rec.forecasted_demand.toLocaleString() }}</td>
                <td class="num">
                  <strong>{{ rec.quantity.toLocaleString() }}</strong>
                  <span v-if="rec.partial" class="badge warning partial-badge" :title="t('restocking.partialHint')">
                    {{ t('restocking.partial') }}
                  </span>
                </td>
                <td class="num">{{ money(rec.unit_cost, 2) }}</td>
                <td class="num"><strong>{{ money(rec.lineTotal, 2) }}</strong></td>
                <td class="num">{{ rec.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="unfunded.length > 0" class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.notFunded') }} ({{ unfunded.length }})</h3>
        </div>
        <p class="unfunded-desc">{{ t('restocking.notFundedDescription', { count: unfunded.length }) }}</p>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in unfunded" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td class="num">{{ item.gap.toLocaleString() }}</td>
                <td class="num">{{ money(item.unit_cost, 2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const toCents = (value) => Math.round(value * 100)

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const demand = ref([])
    const budget = ref(50000)
    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    const money = (amount, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
        : formatCurrency(amount, currentCurrency.value)
    }

    const trendLabel = (trend) => {
      const key = `trends.${trend}`
      const label = t(key)
      return label === key ? trend : label
    }

    // Items with a positive stock gap whose demand is not decreasing, largest gap first
    const candidates = computed(() => {
      return demand.value
        .filter(item => item.trend !== 'decreasing' && item.unit_cost > 0)
        .map(item => ({ ...item, gap: item.forecasted_demand - item.on_hand }))
        .filter(item => item.gap > 0)
        .sort((a, b) => b.gap - a.gap || String(a.item_sku).localeCompare(String(b.item_sku)))
    })

    // Greedy allocation in integer cents to avoid floating point drift
    const allocation = computed(() => {
      let remainingCents = toCents(budget.value)
      const funded = []
      const skipped = []
      for (const item of candidates.value) {
        const unitCents = toCents(item.unit_cost)
        const fullCents = unitCents * item.gap
        if (fullCents <= remainingCents) {
          funded.push({ ...item, quantity: item.gap, partial: false, lineTotal: fullCents / 100 })
          remainingCents -= fullCents
          continue
        }
        const units = Math.floor(remainingCents / unitCents)
        if (units > 0) {
          const lineCents = units * unitCents
          funded.push({ ...item, quantity: units, partial: true, lineTotal: lineCents / 100 })
          remainingCents -= lineCents
        } else {
          skipped.push(item)
        }
      }
      return { funded, skipped }
    })

    const recommendations = computed(() => allocation.value.funded)
    const unfunded = computed(() => allocation.value.skipped)

    const totalSpend = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + toCents(rec.lineTotal), 0) / 100
    })
    const remaining = computed(() => (toCents(budget.value) - toCents(totalSpend.value)) / 100)
    const overallLeadTime = computed(() => {
      return recommendations.value.reduce((max, rec) => Math.max(max, rec.lead_time_days || 0), 0)
    })

    const loadDemand = async () => {
      try {
        loading.value = true
        error.value = null
        demand.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = t('restocking.loadError')
        console.error('Load error:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return
      submitting.value = true
      submitError.value = null
      placedOrder.value = null
      try {
        placedOrder.value = await api.createRestockingOrder({
          budget: budget.value,
          items: recommendations.value.map(rec => ({ sku: rec.item_sku, quantity: rec.quantity }))
        })
      } catch (err) {
        const detail = err.response && err.response.data && err.response.data.detail
        submitError.value = typeof detail === 'string' ? detail : t('restocking.submitError')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadDemand)

    return {
      t,
      loading,
      error,
      budget,
      candidates,
      recommendations,
      unfunded,
      totalSpend,
      remaining,
      overallLeadTime,
      submitting,
      submitError,
      placedOrder,
      money,
      trendLabel,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.375rem;
  font-size: 0.813rem;
  color: #64748b;
}

.hint {
  text-align: center;
}

th.num,
td.num {
  text-align: right;
  white-space: nowrap;
}

.partial-badge {
  margin-left: 0.5rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.success-message a {
  margin-left: 0.5rem;
  color: #2563eb;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.unfunded-desc {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}
</style>
