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
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <div class="budget-body">
          <input
            v-model.number="budget"
            type="range"
            min="0"
            :max="sliderMax"
            step="100"
            class="budget-slider"
            :aria-label="t('restocking.budget')"
            @input="onBudgetInput"
          />
        </div>
      </div>

      <div v-if="reloadError" class="inline-message inline-error">{{ reloadError }}</div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ money(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ money(remaining) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.items') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.items') }} ({{ items.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="items.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderError" class="inline-message inline-error">{{ orderError }}</div>
        <div v-if="placedOrder" class="inline-message inline-success">
          {{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>

        <p v-if="items.length === 0" class="muted-empty">{{ t('restocking.noItems') }}</p>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.demand_gap.toLocaleString() }}</td>
                <td>{{ item.quantity.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ money(item.unit_cost) }}</td>
                <td><strong>{{ currencySymbol }}{{ money(item.line_total) }}</strong></td>
                <td>{{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Costs can have cents (e.g. 42.5); always show exactly two decimals
    const money = (value) => Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    // NOTE: intentionally NOT watching the global filters (useFilters). Demand forecasts
    // have no warehouse/category dimension, so the recommendations cannot be filtered.

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(0)
    const maxBudget = ref(0)
    const items = ref([])
    const totalCost = ref(0)
    const remaining = ref(0)
    const placing = ref(false)
    const orderError = ref(null)
    // Errors from slider-triggered reloads stay inline so the slider remains usable;
    // the page-level `error` is reserved for the initial load failing
    const reloadError = ref(null)

    // max_budget usually has cents, and a range input only lands on multiples of
    // `step`, so round up to the next 100 or "cover every gap" would be unreachable
    const sliderMax = computed(() => Math.ceil(maxBudget.value / 100) * 100)
    const placedOrder = ref(null)

    let debounceTimer = null
    // Monotonic id so a slow, stale response never overwrites a newer one
    let requestSeq = 0

    const applyRecommendations = (data) => {
      items.value = data.items
      totalCost.value = data.total_cost
      remaining.value = data.remaining_budget
    }

    const loadRecommendations = async () => {
      const seq = ++requestSeq
      try {
        const data = await api.getRestockRecommendations(budget.value)
        if (seq !== requestSeq) return
        applyRecommendations(data)
        reloadError.value = null
      } catch (err) {
        if (seq !== requestSeq) return
        reloadError.value = 'Failed to load recommendations: ' + err.message
      }
    }

    // Debounce slider drags so we only call the API once the value settles
    const onBudgetInput = () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 250)
    }

    const init = async () => {
      try {
        // budget=0 yields no items but returns max_budget (cost to cover every gap)
        const base = await api.getRestockRecommendations(0)
        maxBudget.value = base.max_budget
        // Default to 50% of max, rounded to the slider step of 100
        budget.value = Math.round((base.max_budget * 0.5) / 100) * 100
        if (budget.value > 0) {
          await loadRecommendations()
        } else {
          applyRecommendations(base)
        }
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (placing.value || items.value.length === 0) return
      // A pending debounce would leave the table out of sync with the budget being ordered
      clearTimeout(debounceTimer)
      placing.value = true
      orderError.value = null
      placedOrder.value = null
      try {
        placedOrder.value = await api.createRestockOrder(budget.value)
        await loadRecommendations()
      } catch (err) {
        orderError.value = err.response?.data?.detail || err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(init)
    onUnmounted(() => clearTimeout(debounceTimer))

    return {
      t,
      money,
      currencySymbol,
      translateProductName,
      loading,
      error,
      budget,
      maxBudget,
      items,
      totalCost,
      remaining,
      placing,
      orderError,
      reloadError,
      sliderMax,
      placedOrder,
      onBudgetInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
}

.budget-body {
  padding: 0.5rem 1.5rem 1.5rem;
}

.budget-slider {
  width: 100%;
  accent-color: var(--text);
}

.place-order-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-bg);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--primary-bg-hover);
}

.place-order-btn:disabled {
  background: var(--border-strong);
  cursor: not-allowed;
}

.inline-message {
  margin: 0 1.5rem 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.inline-success {
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  color: var(--success-text);
}

.inline-success a {
  margin-left: 0.5rem;
  color: #2563eb;
  font-weight: 500;
}

.inline-error {
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  color: var(--danger-text);
}

.muted-empty {
  padding: 1rem 1.5rem;
  margin: 0;
  color: var(--text-muted);
  font-size: 0.875rem;
}
</style>
