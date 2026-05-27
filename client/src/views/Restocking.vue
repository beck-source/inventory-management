<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetTitle') }}</h3>
        </div>
        <div class="budget-content">
          <div class="budget-label-row">
            <span class="budget-label">{{ t('restocking.budgetLabel') }}</span>
            <span class="budget-amount">{{ formatCurrency(budget) }}</span>
          </div>
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            :min="0"
            :max="maxBudget"
            :step="sliderStep"
          />
          <div class="budget-hint">
            {{ t('restocking.restockEverything', { amount: formatCurrency(maxBudget) }) }}
          </div>
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedTitle') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.emptyState') }}
        </div>
        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.item') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.recommendedQty') }}</th>
                  <th>{{ t('restocking.table.lineCost') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rec in recommendations" :key="rec.sku">
                  <td><strong>{{ rec.sku }}</strong></td>
                  <td>{{ rec.name }}</td>
                  <td>
                    <span :class="['badge', rec.trend]">{{ t('trends.' + rec.trend) }}</span>
                  </td>
                  <td>{{ formatCurrencyDecimals(rec.unit_cost) }}</td>
                  <td>{{ rec.qty }}</td>
                  <td><strong>{{ formatCurrencyDecimals(rec.line_cost) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-footer">
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-label">{{ t('restocking.itemsSelected') }}</span>
                <span class="summary-value">{{ itemCount }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">{{ t('restocking.totalCost') }}</span>
                <span class="summary-value">{{ formatCurrencyDecimals(totalCost) }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">{{ t('restocking.budgetRemaining') }}</span>
                <span class="summary-value">{{ formatCurrencyDecimals(budgetRemaining) }}</span>
              </div>
            </div>

            <div v-if="successMessage" class="success-banner">
              {{ successMessage }}
            </div>

            <div v-if="submitError" class="error submit-error">{{ submitError }}</div>

            <div v-if="!confirming" class="action-row">
              <button
                class="place-order-btn"
                :disabled="itemCount === 0 || submitting"
                @click="confirming = true"
              >
                {{ t('restocking.placeOrder') }}
              </button>
            </div>

            <div v-else class="confirm-panel">
              <p class="confirm-prompt">
                {{ t('restocking.confirmPrompt', { count: itemCount, amount: formatCurrency(totalCost) }) }}
              </p>
              <div class="confirm-actions">
                <button
                  class="confirm-btn"
                  :disabled="submitting"
                  @click="handlePlaceOrder"
                >
                  {{ t('restocking.confirm') }}
                </button>
                <button class="cancel-btn" @click="confirming = false">
                  {{ t('restocking.cancel') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil, formatCurrencyWithDecimals as formatCurrencyDecimalsUtil } from '../utils/currency'

const TREND_RANK = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const submitError = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const confirming = ref(false)
    const submitting = ref(false)
    const successMessage = ref(null)

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const formatCurrencyDecimals = (value) => {
      return formatCurrencyDecimalsUtil(value, currentCurrency.value, 2)
    }

    // Sum of gap * unit_cost for all candidates with gap>0 and unit_cost>0
    const maxBudget = computed(() => {
      return forecasts.value.reduce((sum, f) => {
        const gap = Math.max(f.forecasted_demand - f.current_demand, 0)
        if (gap > 0 && f.unit_cost > 0) {
          return sum + gap * f.unit_cost
        }
        return sum
      }, 0)
    })

    const sliderStep = computed(() => Math.max(1, Math.round(maxBudget.value / 100)))

    // Greedy allocation: sort by trend rank then gap desc, fill up to budget
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          unit_cost: f.unit_cost,
          gap: Math.max(f.forecasted_demand - f.current_demand, 0)
        }))
        .filter(c => c.gap > 0 && c.unit_cost > 0)
        .sort((a, b) => {
          const rankDiff = (TREND_RANK[a.trend] ?? 3) - (TREND_RANK[b.trend] ?? 3)
          if (rankDiff !== 0) return rankDiff
          return b.gap - a.gap
        })

      let remaining = budget.value
      const result = []
      for (const c of candidates) {
        const fullCost = c.gap * c.unit_cost
        const qty = fullCost <= remaining ? c.gap : Math.floor(remaining / c.unit_cost)
        if (qty >= 1) {
          const line_cost = qty * c.unit_cost
          result.push({ ...c, qty, line_cost })
          remaining -= line_cost
        }
      }
      return result
    })

    const totalCost = computed(() => recommendations.value.reduce((sum, r) => sum + r.line_cost, 0))
    const itemCount = computed(() => recommendations.value.length)
    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getDemandForecasts()
        forecasts.value = data
        // Initialize budget to half of max after data is reactive
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const handlePlaceOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const payload = {
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.qty,
            unit_price: r.unit_cost
          })),
          budget: budget.value
        }
        const result = await api.placeRestockOrder(payload)
        successMessage.value = t('restocking.success', { orderNumber: result.order_number })
        confirming.value = false
      } catch (err) {
        submitError.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      submitError,
      budget,
      maxBudget,
      sliderStep,
      recommendations,
      totalCost,
      itemCount,
      budgetRemaining,
      confirming,
      submitting,
      successMessage,
      formatCurrency,
      formatCurrencyDecimals,
      handlePlaceOrder
    }
  }
}
</script>

<style scoped>
.budget-content {
  padding: 0.5rem 0 0.25rem;
}

.budget-label-row {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  accent-color: var(--accent);
  background: var(--border);
  border-radius: 3px;
  cursor: pointer;
  outline: none;
  margin-bottom: 0.75rem;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(249, 115, 22, 0.4);
  transition: box-shadow 0.2s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.5);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 4px rgba(249, 115, 22, 0.4);
}

.budget-hint {
  font-size: 0.813rem;
  color: var(--text-muted);
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.order-footer {
  border-top: 1px solid var(--border);
  margin-top: 1rem;
  padding-top: 1rem;
}

.summary-stats {
  display: flex;
  gap: 2.5rem;
  margin-bottom: 1.25rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--accent);
}

.success-banner {
  background: var(--success-soft);
  color: var(--success);
  border: 1px solid var(--success);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.submit-error {
  margin-bottom: 1rem;
}

.action-row {
  display: flex;
  align-items: center;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: var(--accent-hover);
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.confirm-panel {
  background: var(--bg-inset);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.confirm-prompt {
  font-size: 0.938rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-weight: 500;
}

.confirm-actions {
  display: flex;
  gap: 0.75rem;
}

.confirm-btn {
  padding: 0.625rem 1.5rem;
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.confirm-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.confirm-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 0.625rem 1.25rem;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: var(--bg-elevated);
  border-color: var(--border-strong);
  color: var(--text-primary);
}
</style>
