<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="loadError" class="error">{{ t('restocking.loadFailed') }}</div>
    <div v-else>
      <div v-if="placedOrder" class="success-banner">
        <div>
          <strong>{{ t('restocking.orderPlaced') }}</strong>
          <span>
            {{ t('restocking.orderPlacedDetail', {
              orderNumber: placedOrder.order_number,
              days: placedOrder.lead_time_days
            }) }}
          </span>
        </div>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          :step="BUDGET_STEP"
          :disabled="maxBudget === 0 || submitting"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ currencySymbol }}0</span>
          <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'info']">
          <div class="stat-label">{{ t('restocking.spent') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(spentCents / 100) }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(remainingCents / 100) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ longestLeadTime }} {{ t('restocking.days') }}</div>
        </div>
      </div>

      <div v-if="overBudget" class="warning-banner">
        {{ t('restocking.overBudget', { amount: currencySymbol + formatMoney((spentCents - budgetCents) / 100) }) }}
      </div>
      <div v-if="submitError" class="error">{{ t('restocking.submitFailed') }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ orderedRows.length }})</h3>
          <button
            type="button"
            class="btn-primary"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="rows.length === 0" class="empty-state">{{ t('restocking.noShortfalls') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.stock') }}</th>
                <th class="num">{{ t('restocking.table.forecast') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku">
                <td>
                  <strong>{{ translateProductName(row.name) }}</strong>
                  <div class="sku">{{ row.sku }}</div>
                </td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                </td>
                <td class="num">{{ row.stock }}</td>
                <td class="num">{{ row.forecast }}</td>
                <td class="num">{{ row.shortfall }}</td>
                <td class="num">{{ currencySymbol }}{{ formatMoney(row.unitCostCents / 100) }}</td>
                <td class="num">
                  <input
                    type="number"
                    class="input qty-input"
                    min="0"
                    step="1"
                    :value="row.quantity"
                    :disabled="submitting"
                    :aria-label="t('restocking.table.quantity')"
                    @change="setQuantity(row, $event.target)"
                  />
                </td>
                <td class="num">{{ currencySymbol }}{{ formatMoney(row.lineTotalCents / 100) }}</td>
                <td class="num">{{ row.leadTime }} {{ t('restocking.days') }}</td>
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

const BUDGET_STEP = 100
const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const loadError = ref(false)
    const submitting = ref(false)
    const submitError = ref(false)
    const placedOrder = ref(null)
    const orderLocked = ref(false)
    const forecasts = ref([])
    const budget = ref(0)
    const quantityOverrides = ref({})

    // Money is handled in integer cents to match the server's rounded comparison
    const toCents = (value) => Math.round(value * 100)
    const shortfallOf = (f) => Math.max(0, f.forecasted_demand - f.quantity_on_hand)

    const isRestockCandidate = (f) => {
      return f.unit_cost != null && f.quantity_on_hand != null && f.lead_time_days != null &&
        Number.isFinite(f.forecasted_demand) && shortfallOf(f) > 0
    }

    const candidates = computed(() => forecasts.value.filter(isRestockCandidate))

    const maxBudget = computed(() => {
      const totalCents = candidates.value.reduce((sum, f) => sum + shortfallOf(f) * toCents(f.unit_cost), 0)
      return Math.ceil(totalCents / 100 / BUDGET_STEP) * BUDGET_STEP
    })

    const budgetCents = computed(() => toCents(budget.value))

    // Greedy fill by trend priority, then largest shortfall first
    const recommendations = computed(() => {
      const sorted = [...candidates.value].sort((a, b) => {
        const byTrend = (TREND_ORDER[a.trend] ?? 3) - (TREND_ORDER[b.trend] ?? 3)
        return byTrend !== 0 ? byTrend : shortfallOf(b) - shortfallOf(a)
      })

      let remainingCents = budgetCents.value
      return sorted.map(f => {
        const shortfall = shortfallOf(f)
        const unitCostCents = toCents(f.unit_cost)
        const affordable = unitCostCents > 0 ? Math.floor(remainingCents / unitCostCents) : shortfall
        const quantity = Math.min(shortfall, affordable)
        remainingCents -= quantity * unitCostCents
        return { forecast: f, shortfall, quantity, unitCostCents }
      })
    })

    const rows = computed(() => {
      return recommendations.value.map(({ forecast: f, shortfall, quantity, unitCostCents }) => {
        const override = quantityOverrides.value[f.item_sku]
        const finalQuantity = override !== undefined ? override : quantity
        return {
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          stock: f.quantity_on_hand,
          forecast: f.forecasted_demand,
          shortfall,
          unitCostCents,
          quantity: finalQuantity,
          lineTotalCents: finalQuantity * unitCostCents,
          leadTime: f.lead_time_days
        }
      })
    })

    const orderedRows = computed(() => rows.value.filter(r => r.quantity > 0))

    const spentCents = computed(() => rows.value.reduce((sum, r) => sum + r.lineTotalCents, 0))
    const remainingCents = computed(() => budgetCents.value - spentCents.value)
    const overBudget = computed(() => spentCents.value > budgetCents.value)
    const longestLeadTime = computed(() => {
      return orderedRows.value.reduce((max, r) => Math.max(max, r.leadTime), 0)
    })

    const canPlaceOrder = computed(() => {
      return !submitting.value && !orderLocked.value && !overBudget.value && orderedRows.value.length > 0
    })

    const formatMoney = (value) => {
      return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    // A placed order stays locked until the plan changes, so it cannot be submitted twice
    const unlockOrder = () => {
      orderLocked.value = false
      placedOrder.value = null
    }

    const setQuantity = (row, input) => {
      const parsed = Math.floor(Number(input.value))
      const quantity = Number.isFinite(parsed) && parsed > 0 ? parsed : 0
      input.value = String(quantity)
      if (quantity === row.quantity) return
      quantityOverrides.value = { ...quantityOverrides.value, [row.sku]: quantity }
      unlockOrder()
    }

    watch(budget, () => {
      quantityOverrides.value = {}
      unlockOrder()
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        loadError.value = false
        forecasts.value = await api.getDemandForecasts()
        budget.value = Math.round(maxBudget.value / 2 / BUDGET_STEP) * BUDGET_STEP
      } catch (err) {
        loadError.value = true
        console.error('Failed to load demand forecasts:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      submitting.value = true
      submitError.value = false
      placedOrder.value = null
      try {
        placedOrder.value = await api.createRestockingOrder({
          budget: budget.value,
          items: orderedRows.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
        orderLocked.value = true
      } catch (err) {
        submitError.value = true
        console.error('Failed to place restocking order:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      BUDGET_STEP,
      currencySymbol,
      loading,
      loadError,
      submitting,
      submitError,
      placedOrder,
      budget,
      maxBudget,
      rows,
      orderedRows,
      budgetCents,
      spentCents,
      remainingCents,
      overBudget,
      longestLeadTime,
      canPlaceOrder,
      formatMoney,
      setQuantity,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.card-header {
  flex-wrap: wrap;
}

.budget-value {
  font-size: var(--text-xl);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.budget-slider {
  width: 100%;
  accent-color: var(--color-primary);
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  color: var(--color-text-muted);
}

.success-banner,
.warning-banner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3) var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-6);
  font-size: var(--text-sm);
}

.success-banner {
  background: var(--color-success-soft);
  border: 1px solid color-mix(in srgb, var(--color-success) 30%, transparent);
  color: var(--color-success-text);
}

.success-banner span {
  margin-left: var(--space-2);
}

.banner-link {
  color: var(--color-success-text);
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.warning-banner {
  background: var(--color-warning-soft);
  border: 1px solid color-mix(in srgb, var(--color-warning) 30%, transparent);
  color: var(--color-warning-text);
}

.sku {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.qty-input {
  width: 80px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
