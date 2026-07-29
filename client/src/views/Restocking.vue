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
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetTitle') }}</h3>
        </div>
        <div class="budget-body">
          <div class="budget-row">
            <input
              type="range"
              class="budget-slider"
              v-model.number="budget"
              min="0"
              max="5000"
              step="100"
            >
            <div class="budget-display">{{ formatCurrency(budget, currentCurrency) }}</div>
          </div>
          <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ plan.selected.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(plan.totalCost, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(plan.remaining, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.daysLead', { days: plan.maxLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="submittedOrder" class="success-banner">
        {{ t('restocking.orderPlaced', { orderNumber: submittedOrder.order_number }) }}
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>
      <div v-else-if="submitError" class="error">
        {{ t('restocking.orderFailed', { message: submitError }) }}
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
            :disabled="submitting || plan.selected.length === 0 || submittedOrder !== null"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="plan.selected.length === 0" class="empty-state">
          {{ candidates.length === 0 ? t('restocking.noShortfall') : t('restocking.noRecommendations') }}
        </div>
        <div v-if="candidates.length > 0" class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in plan.selected" :key="c.item_sku">
                <td>{{ c.item_sku }}</td>
                <td>{{ c.item_name }}</td>
                <td>{{ c.current_demand }}</td>
                <td>{{ c.forecasted_demand }}</td>
                <td>{{ c.shortfall }}</td>
                <td>{{ formatCurrencyWithDecimals(c.unit_cost, currentCurrency, 2) }}</td>
                <td>{{ c.recommended_qty }}</td>
                <td>{{ formatCurrencyWithDecimals(c.line_total, currentCurrency, 2) }}</td>
                <td>{{ t('restocking.daysLead', { days: c.lead_time_days }) }}</td>
              </tr>
              <tr v-for="c in plan.skipped" :key="c.item_sku" class="row-skipped">
                <td>{{ c.item_sku }}</td>
                <td>{{ c.item_name }}</td>
                <td>{{ c.current_demand }}</td>
                <td>{{ c.forecasted_demand }}</td>
                <td>{{ c.shortfall }}</td>
                <td>{{ formatCurrencyWithDecimals(c.unit_cost, currentCurrency, 2) }}</td>
                <td><span class="badge warning">{{ t('restocking.overBudget') }}</span></td>
                <td>{{ formatCurrencyWithDecimals(c.line_total, currentCurrency, 2) }}</td>
                <td>{{ t('restocking.daysLead', { days: c.lead_time_days }) }}</td>
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
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_EPSILON = 0.01

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)

    const budget = ref(2500)

    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrder = ref(null)

    const candidates = computed(() =>
      forecasts.value
        .map(f => {
          const shortfall = f.forecasted_demand - f.current_demand
          return {
            id: f.id,
            item_sku: f.item_sku,
            item_name: f.item_name,
            current_demand: f.current_demand,
            forecasted_demand: f.forecasted_demand,
            unit_cost: f.unit_cost,
            lead_time_days: f.lead_time_days,
            shortfall,
            recommended_qty: shortfall,
            line_total: Math.round(shortfall * f.unit_cost * 100) / 100
          }
        })
        .filter(c => c.shortfall > 0)
        // tie-break on id asc: WDG-001 and FLT-405 both have shortfall 150
        .sort((a, b) => b.shortfall - a.shortfall || Number(a.id) - Number(b.id))
    )

    const plan = computed(() => {
      let remaining = budget.value
      const selected = []
      const skipped = []
      for (const c of candidates.value) {
        if (c.line_total <= remaining + BUDGET_EPSILON) {
          selected.push(c)
          remaining = Math.round((remaining - c.line_total) * 100) / 100
        } else {
          skipped.push(c) // skip and continue — no partial quantities
        }
      }
      const totalCost = Math.round(selected.reduce((s, c) => s + c.line_total, 0) * 100) / 100
      return {
        selected,
        skipped,
        totalCost,
        remaining,
        maxLeadTime: selected.length ? Math.max(...selected.map(c => c.lead_time_days)) : 0
      }
    })

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (submitting.value || plan.value.selected.length === 0 || submittedOrder.value) return
      try {
        submitting.value = true
        submitError.value = null
        submittedOrder.value = await api.createRestockOrder({
          budget: budget.value,
          items: plan.value.selected.map(c => ({
            item_sku: c.item_sku,
            item_name: c.item_name,
            quantity: c.recommended_qty,
            unit_cost: c.unit_cost,
            lead_time_days: c.lead_time_days,
            line_total: c.line_total
          }))
        })
      } catch (err) {
        submitError.value = err.response?.data?.detail || err.message
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      submittedOrder.value = null
      submitError.value = null
    })

    onMounted(() => loadData())

    return {
      t,
      currentCurrency,
      formatCurrency,
      formatCurrencyWithDecimals,
      forecasts,
      loading,
      error,
      budget,
      candidates,
      plan,
      submitting,
      submitError,
      submittedOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card {
  margin-bottom: 1.5rem;
}

.budget-body {
  padding: 1.5rem;
}

.budget-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-display {
  min-width: 140px;
  text-align: right;
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-help {
  margin: 0.75rem 0 0;
  font-size: 0.813rem;
  color: #64748b;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  color: #047857;
  font-weight: 500;
}

.success-banner a {
  color: #059669;
  font-weight: 600;
  text-decoration: underline;
}

.place-order-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  background: #3b82f6;
  color: white;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  transform: none;
}

.row-skipped {
  opacity: 0.5;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
