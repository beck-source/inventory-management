<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget slider -->
    <div class="card budget-card">
      <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
      <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      <input
        type="range"
        class="budget-slider"
        min="0"
        max="30000"
        step="500"
        v-model.number="budget"
        :aria-label="t('restocking.budgetLabel')"
      />
      <div class="budget-meta">
        <span class="badge info">
          {{ t('restocking.coverage', { covered: recommendation.items_covered, total: recommendation.items_total }) }}
        </span>
        <span class="budget-spend">
          {{ t('restocking.plannedSpend') }}: <strong>{{ currencySymbol }}{{ recommendation.total_cost.toLocaleString() }}</strong>
        </span>
      </div>
      <div class="budget-hint">{{ t('restocking.budgetHint') }}</div>
    </div>

    <!-- Recommendations -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendation.items.length === 0" class="empty-state">
        {{ t('restocking.noShortages') }}
      </div>
      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.item') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th class="num">{{ t('restocking.table.shortage') }}</th>
              <th class="num">{{ t('restocking.table.unitCost') }}</th>
              <th class="num">{{ t('restocking.table.lineCost') }}</th>
              <th class="num">{{ t('restocking.table.leadTime') }}</th>
              <th>{{ t('restocking.table.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in recommendation.items"
              :key="item.sku"
              :class="{ 'row-excluded': !item.included }"
            >
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ translateProductName(item.name) }}</td>
              <td><span :class="['trend-chip', trendClass(item.trend)]">{{ trendArrow(item.trend) }}</span></td>
              <td class="num">{{ item.shortage.toLocaleString() }}</td>
              <td class="num">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
              <td class="num"><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
              <td class="num">{{ t('restocking.leadDays', { days: item.lead_time_days }) }}</td>
              <td>
                <span :class="['badge', item.included ? 'success' : 'danger']">
                  {{ item.included ? t('restocking.inBudget') : t('restocking.overBudget') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="action-row">
        <span v-if="successMessage" class="success-message">{{ successMessage }}</span>
        <span v-if="submitError" class="error inline-error">{{ submitError }}</span>
        <button
          class="primary-button"
          :disabled="recommendation.items_covered === 0 || submitting"
          @click="submitOrder"
        >
          {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    // State
    const budget = ref(15000)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)
    const recommendation = ref({ items: [], items_covered: 0, items_total: 0, total_cost: 0 })

    const includedItems = computed(() => recommendation.value.items.filter(i => i.included))

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendation.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = t('common.error') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce slider changes so we don't hit the API on every pixel of drag.
    // 300ms is short enough to feel live but coalesces a continuous drag into
    // one request once the user pauses.
    let debounceTimer = null
    watch(budget, () => {
      successMessage.value = null
      submitError.value = null
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    })
    onBeforeUnmount(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
    })

    const submitOrder = async () => {
      if (includedItems.value.length === 0) return
      try {
        submitting.value = true
        submitError.value = null
        // quantity = shortage: the recommendation is to buy exactly the
        // forecast gap, no safety stock multiplier in this demo.
        const payload = {
          budget: budget.value,
          items: includedItems.value.map(i => ({
            sku: i.sku,
            quantity: i.shortage,
            unit_cost: i.unit_cost
          }))
        }
        const order = await api.submitRestockOrder(payload)
        successMessage.value = t('restocking.submitted', {
          orderNumber: order.order_number,
          count: order.items.length,
          total: currencySymbol.value + order.total_value.toLocaleString()
        })
        // Re-fetch so the table reflects backend state after the submit.
        await loadRecommendations()
      } catch (err) {
        submitError.value = t('restocking.submitError')
      } finally {
        submitting.value = false
      }
    }

    const trendArrow = (trend) => {
      const map = { increasing: '↑', stable: '→', decreasing: '↓' }
      return map[trend] || '→'
    }
    const trendClass = (trend) => `trend-${trend}`

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      translateProductName,
      budget,
      loading,
      error,
      submitting,
      submitError,
      successMessage,
      recommendation,
      includedItems,
      submitOrder,
      trendArrow,
      trendClass
    }
  }
}
</script>

<style scoped>
/* Budget card */
.budget-card {
  margin-bottom: 1.5rem;
}
.budget-label {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.25rem;
}
.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 1rem;
  font-variant-numeric: tabular-nums;
}
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  margin-bottom: 1rem;
  cursor: pointer;
}
.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
}
.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
}
.budget-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.budget-spend {
  font-size: 0.875rem;
  color: #334155;
}
.budget-hint {
  font-size: 0.813rem;
  color: #64748b;
}

/* Table */
.restock-table {
  width: 100%;
  border-collapse: collapse;
}
.restock-table th,
.restock-table td {
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
}
.restock-table th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  font-weight: 600;
}
.restock-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.row-excluded {
  opacity: 0.5;
}

/* Trend chip */
.trend-chip {
  display: inline-block;
  font-weight: 700;
  font-size: 1rem;
}
.trend-increasing { color: #059669; }
.trend-stable { color: #64748b; }
.trend-decreasing { color: #dc2626; }

/* Empty state */
.empty-state {
  padding: 3rem 1rem;
  text-align: center;
  color: #64748b;
}

/* Actions */
.action-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 1rem;
  border-top: 1px solid #f1f5f9;
}
.success-message {
  color: #059669;
  font-size: 0.875rem;
  font-weight: 500;
}
.inline-error {
  font-size: 0.875rem;
}
.primary-button {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 0.625rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}
.primary-button:hover:not(:disabled) {
  background: #1e293b;
}
.primary-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
