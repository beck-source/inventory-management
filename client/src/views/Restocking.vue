<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.budget') }}</div>
        <div class="stat-value">{{ money(budget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
        <div class="stat-value">{{ money(totalCost) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.remaining') }}</div>
        <div class="stat-value">{{ money(remainingBudget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.items') }}</div>
        <div class="stat-value">{{ items.length }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetControl') }}</h3>
      </div>
      <div class="budget-control">
        <input
          v-model.number="budget"
          type="range"
          min="0"
          :max="maxBudget"
          step="500"
          class="budget-slider"
          :aria-label="t('restocking.budgetControl')"
        />
        <div class="budget-input-group">
          <label for="budget-input">{{ t('restocking.budgetInput') }}</label>
          <input
            id="budget-input"
            v-model.number="budget"
            type="number"
            min="0"
            :max="maxBudget"
            step="1"
            class="budget-number"
          />
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
        <button
          type="button"
          class="btn-primary"
          :disabled="!canPlaceOrder"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="confirmation" class="confirmation" role="status">
        <strong>{{ t('restocking.orderPlaced', { orderNumber: confirmation.order_number }) }}</strong>
        <span>
          {{ t('restocking.orderSummary', {
            total: money(confirmation.total_cost),
            leadTime: t('common.days', { n: confirmation.lead_time_days }),
            delivery: formatDate(confirmation.expected_delivery)
          }) }}
        </span>
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div v-if="loading && items.length === 0" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="items.length === 0" class="empty-note">{{ t('restocking.empty') }}</div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.sku') }}</th>
              <th>{{ t('restocking.name') }}</th>
              <th>{{ t('restocking.trend') }}</th>
              <th class="num">{{ t('restocking.quantity') }}</th>
              <th class="num">{{ t('restocking.unitCost') }}</th>
              <th class="num">{{ t('restocking.lineTotal') }}</th>
              <th class="num">{{ t('restocking.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.sku">
              <td class="mono"><strong>{{ item.sku }}</strong></td>
              <td>{{ translateProductName(item.name) }}</td>
              <td>
                <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
              </td>
              <td class="num">{{ item.quantity }}</td>
              <td class="num">{{ moneyExact(item.unit_cost) }}</td>
              <td class="num"><strong>{{ moneyExact(item.line_total) }}</strong></td>
              <td class="num">{{ t('common.days', { n: item.lead_time_days }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const SLIDER_STEP = 500
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    // Budget is always held and sent in USD; only display is converted
    const budget = ref(2500)
    const fullCost = ref(0)
    const items = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(2500)
    const loading = ref(true)
    const error = ref(null)

    const submitting = ref(false)
    // True from a budget change until its debounced reload starts; items are stale meanwhile
    const pending = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    // Slider max: cost of restocking everything, rounded up to the next 500 step
    const maxBudget = computed(() => {
      return Math.max(SLIDER_STEP, Math.ceil(fullCost.value / SLIDER_STEP) * SLIDER_STEP)
    })

    const money = (amount) => formatCurrency(amount, currentCurrency.value)
    const moneyExact = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return ''
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // Number input can yield '' / null / negatives while typing; coerce to a valid budget
    const sanitizedBudget = () => {
      const value = Number(budget.value)
      return Number.isFinite(value) && value > 0 ? value : 0
    }

    // Guards against out-of-order responses: only the latest request may update state
    let requestId = 0
    const loadRecommendations = async () => {
      const current = ++requestId
      pending.value = false
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(sanitizedBudget())
        if (current !== requestId) return
        items.value = data.items
        totalCost.value = data.total_cost
        remainingBudget.value = data.remaining_budget
        fullCost.value = data.full_cost
      } catch (err) {
        if (current !== requestId) return
        // Drop stale items so they cannot be ordered while the table is hidden
        items.value = []
        error.value = t('restocking.loadFailed')
        console.error('Load error:', err)
      } finally {
        if (current === requestId) loading.value = false
      }
    }

    let debounceTimer = null
    watch(budget, () => {
      // Keep the budget within slider bounds when typed manually
      if (budget.value > maxBudget.value && fullCost.value > 0) {
        // Assigning re-triggers this watcher, which then schedules the fetch
        budget.value = maxBudget.value
        return
      }
      pending.value = true
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })

    // Only allow ordering items that match the budget currently shown
    const canPlaceOrder = computed(() =>
      items.value.length > 0 && !submitting.value && !loading.value && !pending.value && !error.value
    )

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      submitting.value = true
      submitError.value = null
      confirmation.value = null
      try {
        confirmation.value = await api.submitRestockOrder(
          items.value.map(({ sku, quantity }) => ({ sku, quantity }))
        )
      } catch (err) {
        submitError.value = t('restocking.submitFailed')
        console.error('Submit error:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)
    onUnmounted(() => clearTimeout(debounceTimer))

    return {
      t,
      canPlaceOrder,
      budget,
      maxBudget,
      items,
      totalCost,
      remainingBudget,
      loading,
      error,
      submitting,
      submitError,
      confirmation,
      money,
      moneyExact,
      formatDate,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-2) var(--space-6) var(--space-6);
}

.budget-slider {
  flex: 1;
  accent-color: var(--text);
}

.budget-input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.budget-number {
  width: 140px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  font-size: var(--text-base);
}

.confirmation {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin: 0 var(--space-6) var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--success-soft);
  border: 1px solid var(--success-border);
  border-radius: var(--radius-md);
  color: var(--text);
  font-size: var(--text-base);
}

.confirmation-link {
  color: var(--info);
  font-weight: 500;
}

.empty-note {
  padding: var(--space-6);
  color: var(--text-muted);
  font-size: var(--text-base);
}

th.num,
td.num {
  text-align: right;
}
</style>
