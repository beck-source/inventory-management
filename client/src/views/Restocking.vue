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
        <div class="budget-row">
          <label class="budget-label" for="restock-budget">{{ t('restocking.budgetSlider') }}</label>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          id="restock-budget"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="BUDGET_STEP"
        />
        <div class="budget-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.spent') }}</div>
          <div class="stat-value">{{ money(totalSpent) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(remainingBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ overallLeadTime === null ? '-' : t('restocking.days', { count: overallLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="placedOrder" class="confirmation" role="status">
        <h3 class="confirmation-title">{{ t('restocking.confirmation.title') }}</h3>
        <dl class="confirmation-details">
          <div>
            <dt>{{ t('restocking.confirmation.orderNumber') }}</dt>
            <dd>{{ placedOrder.order_number }}</dd>
          </div>
          <div>
            <dt>{{ t('restocking.confirmation.total') }}</dt>
            <dd>{{ money(placedOrder.total_value) }}</dd>
          </div>
          <div>
            <dt>{{ t('restocking.confirmation.leadTime') }}</dt>
            <dd>{{ t('restocking.days', { count: placedOrder.lead_time_days }) }}</dd>
          </div>
          <div>
            <dt>{{ t('restocking.confirmation.expectedDelivery') }}</dt>
            <dd>{{ formatDate(placedOrder.expected_delivery) }}</dd>
          </div>
        </dl>
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.confirmation.viewOrders') }}</router-link>
      </div>

      <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.growth') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ translateProductName(rec.item_name) }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ trendLabel(rec.trend) }}</span>
                </td>
                <td class="num">{{ formatGrowth(rec.growth_pct) }}</td>
                <td class="num">{{ rec.quantity }}</td>
                <td class="num">{{ money(rec.unit_cost) }}</td>
                <td class="num"><strong>{{ money(rec.line_cost) }}</strong></td>
                <td>{{ rec.supplier_name }}</td>
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
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const BUDGET_STEP = 500

export default {
  name: 'Restocking',
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const budget = ref(0)

    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    // Items worth restocking; flat/declining items come back with suggested_qty 0
    const candidates = computed(() => {
      return items.value
        .filter(item => item.suggested_qty > 0)
        .sort((a, b) => b.growth_pct - a.growth_pct)
    })

    // Slider ceiling: cost of buying every suggestion, rounded up to the next 1000
    // so the right end of the slider always funds the full recommendation.
    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, item) => sum + item.suggested_qty * item.unit_cost, 0)
      return Math.ceil(total / 1000) * 1000
    })

    // Greedy fill by growth rate. Runs as a computed so slider moves update instantly
    // without an API call.
    const recommendations = computed(() => {
      // Work in integer cents so float drift in unit_cost can never push spend over budget.
      let remainingCents = Math.round(budget.value * 100)
      const picked = []

      for (const item of candidates.value) {
        const unitCents = Math.round(item.unit_cost * 100)
        if (unitCents <= 0) continue
        const qty = Math.min(item.suggested_qty, Math.floor(remainingCents / unitCents))
        // Keep scanning after a miss: a cheaper, lower-growth item may still fit.
        if (qty >= 1) {
          remainingCents -= qty * unitCents
          picked.push({ ...item, quantity: qty, line_cost: (qty * unitCents) / 100 })
        }
      }
      return picked
    })

    const totalSpent = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + Math.round(rec.line_cost * 100), 0) / 100
    })

    const remainingBudget = computed(() => Math.max(0, budget.value - totalSpent.value))

    // The order ships when its slowest item arrives
    const overallLeadTime = computed(() => {
      if (recommendations.value.length === 0) return null
      return Math.max(...recommendations.value.map(rec => rec.lead_time_days))
    })

    const money = (amount) => formatCurrency(amount, currentCurrency.value)

    const trendLabel = (trend) => {
      return ['increasing', 'stable', 'decreasing'].includes(trend) ? t(`trends.${trend}`) : trend
    }

    const formatGrowth = (pct) => `${pct > 0 ? '+' : ''}${Number(pct).toFixed(1)}%`

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadItems = async () => {
      try {
        loading.value = true
        error.value = null
        items.value = await api.getRestockItems()
        // Default to half of max, snapped to the slider step so the thumb sits on a valid value.
        budget.value = Math.round((maxBudget.value * 0.5) / BUDGET_STEP) * BUDGET_STEP
      } catch (err) {
        error.value = t('restocking.loadError')
        console.error('Failed to load restock items:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (submitting.value || recommendations.value.length === 0) return
      submitting.value = true
      submitError.value = null
      placedOrder.value = null
      try {
        // Only sku and quantity are sent; the server owns pricing.
        placedOrder.value = await api.createRestockOrder({
          items: recommendations.value.map(rec => ({ item_sku: rec.item_sku, quantity: rec.quantity }))
        })
      } catch (err) {
        const detail = err.response?.data?.detail
        // 422 responses carry a validation array rather than a string, so fall back to the generic message.
        submitError.value = typeof detail === 'string' ? detail : t('restocking.submitError')
        console.error('Failed to place restock order:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadItems)

    return {
      t,
      BUDGET_STEP,
      loading,
      error,
      budget,
      maxBudget,
      recommendations,
      totalSpent,
      remainingBudget,
      overallLeadTime,
      submitting,
      submitError,
      placedOrder,
      money,
      trendLabel,
      formatGrowth,
      formatDate,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.813rem;
}

.num {
  text-align: right;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: #ffffff;
  border: 1px solid #0f172a;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #e2e8f0;
  border-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.confirmation {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}

.confirmation-title {
  color: #065f46;
  font-size: 1.063rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.confirmation-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.confirmation-details dt {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.confirmation-details dd {
  color: #0f172a;
  font-weight: 600;
}

.confirmation-link {
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
}

.confirmation-link:hover {
  text-decoration: underline;
}
</style>
