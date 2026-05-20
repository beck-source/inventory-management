<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="loadError" class="error">{{ loadError }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
        </div>
        <div class="budget-row">
          <div class="budget-slider">
            <input
              type="range"
              :min="0"
              :max="maxBudget"
              :step="sliderStep"
              v-model.number="budget"
              class="slider"
              aria-label="Budget"
            />
            <div class="slider-track-meta">
              <span>{{ currencySymbol }}0</span>
              <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
            </div>
          </div>
          <div class="budget-readout">
            <div class="budget-label">{{ t('restocking.budget.label') }}</div>
            <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
            <div class="budget-remaining">
              {{ t('restocking.budget.remaining') }}:
              <strong>{{ currencySymbol }}{{ remaining.toLocaleString() }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations.title') }}
            <span class="count-chip">{{ recommendations.length }}</span>
          </h3>
          <div class="header-totals">
            <span class="total-pill">
              {{ t('restocking.recommendations.totalCost') }}:
              <strong>{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</strong>
            </span>
            <span v-if="recommendations.length" class="total-pill">
              {{ t('restocking.recommendations.maxLeadTime') }}:
              <strong>{{ maxLeadTime }} {{ t('restocking.recommendations.days') }}</strong>
            </span>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.recommendations.empty') }}
        </div>
        <div v-else class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recommendations" :key="row.sku">
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>
                  <span :class="['badge', row.trend]">
                    {{ t(`restocking.trend.${row.trend}`) }}
                  </span>
                </td>
                <td class="num">{{ row.quantity.toLocaleString() }}</td>
                <td class="num">{{ currencySymbol }}{{ row.unit_cost.toFixed(2) }}</td>
                <td class="num"><strong>{{ currencySymbol }}{{ row.line_total.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</strong></td>
                <td class="num">{{ row.lead_time_days }} {{ t('restocking.recommendations.days') }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="actions">
          <div v-if="submitSuccess" class="success-banner">
            {{ t('restocking.submit.success', { orderNumber: submitSuccess.order_number }) }}
          </div>
          <div v-if="submitError" class="error">{{ submitError }}</div>
          <button
            class="place-order-btn"
            :disabled="!recommendations.length || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submit.submitting') : t('restocking.submit.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const TREND_PRIORITY = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const loading = ref(true)
    const loadError = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const submitSuccess = ref(null)

    const inventory = ref([])
    const demand = ref([])
    const budget = ref(0)

    // Index inventory by SKU once for quick joins.
    const inventoryBySku = computed(() => {
      const map = new Map()
      for (const item of inventory.value) {
        map.set(item.sku, item)
      }
      return map
    })

    // Candidates: demand forecast joined with inventory (skip forecast items
    // whose SKU has no inventory record — we can't price/lead-time them).
    const candidates = computed(() => {
      const rows = []
      for (const f of demand.value) {
        const inv = inventoryBySku.value.get(f.item_sku)
        if (!inv) continue
        rows.push({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          forecasted_demand: f.forecasted_demand,
          unit_cost: inv.unit_cost,
          lead_time_days: inv.lead_time_days
        })
      }
      // Sort by trend priority, then by potential spend (desc).
      rows.sort((a, b) => {
        const tp = (TREND_PRIORITY[a.trend] ?? 99) - (TREND_PRIORITY[b.trend] ?? 99)
        if (tp !== 0) return tp
        return (b.forecasted_demand * b.unit_cost) - (a.forecasted_demand * a.unit_cost)
      })
      return rows
    })

    const maxBudget = computed(() => 250000)

    const sliderStep = computed(() => 1000)

    // Greedy recommendation: take full forecasted demand per item until budget
    // runs out, then take a partial quantity of the next item if any fits.
    const recommendations = computed(() => {
      const picks = []
      let remaining = budget.value
      for (const c of candidates.value) {
        if (remaining < c.unit_cost) continue
        const maxAffordable = Math.floor(remaining / c.unit_cost)
        const qty = Math.min(c.forecasted_demand, maxAffordable)
        if (qty <= 0) continue
        const lineTotal = qty * c.unit_cost
        picks.push({
          sku: c.sku,
          name: c.name,
          trend: c.trend,
          quantity: qty,
          unit_cost: c.unit_cost,
          lead_time_days: c.lead_time_days,
          line_total: lineTotal
        })
        remaining -= lineTotal
      }
      return picks
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.line_total, 0)
    )

    const remaining = computed(() => Math.max(0, budget.value - totalCost.value))

    const maxLeadTime = computed(() => {
      if (!recommendations.value.length) return 0
      return Math.max(...recommendations.value.map((r) => r.lead_time_days))
    })

    const loadData = async () => {
      try {
        loading.value = true
        loadError.value = null
        const [inv, dem] = await Promise.all([
          api.getInventory({}),
          api.getDemandForecasts()
        ])
        inventory.value = inv
        demand.value = dem
        // Default to half of maxBudget so the user sees a populated table immediately.
        budget.value = Math.round(maxBudget.value / 2 / sliderStep.value) * sliderStep.value
      } catch (err) {
        loadError.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (!recommendations.value.length || submitting.value) return
      submitting.value = true
      submitError.value = null
      submitSuccess.value = null
      try {
        const payload = {
          budget: budget.value,
          items: recommendations.value.map((r) => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days
          }))
        }
        submitSuccess.value = await api.submitRestockingOrder(payload)
      } catch (err) {
        submitError.value = err?.response?.data?.detail || 'Failed to submit order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      currencySymbol,
      loading,
      loadError,
      submitting,
      submitError,
      submitSuccess,
      budget,
      maxBudget,
      sliderStep,
      recommendations,
      totalCost,
      remaining,
      maxLeadTime,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: 2rem;
  align-items: center;
}

.budget-slider {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.slider {
  width: 100%;
  appearance: none;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.slider-track-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.budget-readout {
  text-align: right;
}

.budget-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  font-weight: 600;
}

.budget-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin: 0.125rem 0;
}

.budget-remaining {
  font-size: 0.813rem;
  color: #64748b;
}

.count-chip {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.125rem 0.5rem;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.header-totals {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.total-pill {
  font-size: 0.813rem;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
}

.total-pill strong {
  color: #0f172a;
  margin-left: 0.25rem;
}

.restocking-table th.num,
.restocking-table td.num {
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.place-order-btn {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  transform: translateY(-1px);
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  width: 100%;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
