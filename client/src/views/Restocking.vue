<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Budget slider card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetCard.title') }}</h3>
        </div>
        <div class="budget-controls">
          <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
          <div class="slider-row">
            <span class="slider-label">{{ currencySymbol }}10K</span>
            <input
              type="range"
              class="budget-slider"
              min="10000"
              max="500000"
              step="10000"
              v-model.number="budget"
            />
            <span class="slider-label">{{ currencySymbol }}500K</span>
          </div>
          <p class="budget-help">{{ t('restocking.budgetCard.help') }}</p>
        </div>
      </div>

      <!-- Recommendations card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations.title') }}</h3>
        </div>

        <!-- Success banner: shown after a successful order placement -->
        <div v-if="successMessage" class="success-banner">
          {{ successMessage }}
        </div>

        <!-- Summary stat cards -->
        <div class="stats-grid">
          <div class="stat-card info">
            <div class="stat-label">{{ t('restocking.recommendations.summaryItems') }}</div>
            <div class="stat-value">{{ recommendations.length }}</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">{{ t('restocking.recommendations.summarySpend') }}</div>
            <div class="stat-value">{{ currencySymbol }}{{ totalSpend.toLocaleString() }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('restocking.recommendations.summaryRemaining') }}</div>
            <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
          </div>
        </div>

        <!-- Empty / insufficient state -->
        <div v-if="recommendations.length === 0" class="empty-state">
          <span v-if="hasCandidates">{{ t('restocking.recommendations.insufficient') }}</span>
          <span v-else>{{ t('restocking.recommendations.empty') }}</span>
        </div>

        <!-- Recommendations table -->
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recommendations" :key="row.sku">
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ row.name }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ t('trends.' + row.trend) }}</span>
                </td>
                <td>{{ row.qty }}</td>
                <td>{{ currencySymbol }}{{ row.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ row.lineTotal.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Place Order button -->
        <div class="action-row">
          <button
            class="btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    // Mirror the currency symbol pattern from Orders.vue (lines 92-94)
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const budget = ref(100000)
    const submitting = ref(false)
    const successMessage = ref('')

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        allForecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    /**
     * Greedy partial-fill algorithm:
     * Sort candidates by demand gap (largest shortfall first) so the biggest
     * needs get funded before the budget runs dry. For each candidate, take
     * min(gap, floor(remaining / unit_cost)) so the budget visibly binds —
     * a partially-affordable item still consumes as many units as the budget
     * allows, and leftover budget can fund cheaper items further down the list.
     */
    const recommendations = computed(() => {
      const candidates = allForecasts.value
        .filter(item => (item.forecasted_demand - item.current_demand) > 0)
        .map(item => ({
          sku: item.item_sku,
          name: item.item_name,
          trend: item.trend,
          unit_cost: item.unit_cost,
          gap: item.forecasted_demand - item.current_demand
        }))
        .sort((a, b) => b.gap - a.gap) // largest shortfall first

      let remaining = budget.value
      const result = []

      for (const candidate of candidates) {
        // Affordable quantity: capped at the demand gap so we don't over-order
        const qty = Math.min(candidate.gap, Math.floor(remaining / candidate.unit_cost))
        if (qty >= 1) {
          const lineTotal = qty * candidate.unit_cost
          result.push({
            sku: candidate.sku,
            name: candidate.name,
            trend: candidate.trend,
            unit_cost: candidate.unit_cost,
            qty,
            lineTotal
          })
          remaining -= lineTotal
        }
      }

      return result
    })

    // True if any forecast item has a positive demand gap (regardless of budget)
    const hasCandidates = computed(() =>
      allForecasts.value.some(item => (item.forecasted_demand - item.current_demand) > 0)
    )

    const totalSpend = computed(() =>
      recommendations.value.reduce((sum, row) => sum + row.lineTotal, 0)
    )

    const remainingBudget = computed(() => budget.value - totalSpend.value)

    const placeOrder = async () => {
      submitting.value = true
      successMessage.value = ''
      try {
        const items = recommendations.value.map(r => ({
          sku: r.sku,
          name: r.name,
          quantity: r.qty,
          unit_price: r.unit_cost
        }))
        const order = await api.submitRestockOrder({ items })
        successMessage.value = t('restocking.success', { orderNumber: order.order_number })
      } catch (err) {
        error.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      submitting,
      successMessage,
      recommendations,
      hasCandidates,
      totalSpend,
      remainingBudget,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* Budget slider section */
.budget-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0 0.5rem;
}

.budget-readout {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  max-width: 600px;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.budget-help {
  font-size: 0.875rem;
  color: #64748b;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  border-radius: 8px;
  padding: 0.875rem 1rem;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

/* Empty / insufficient message */
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Place Order button row */
.action-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1.25rem;
}

/* Primary button — mirrors #2563eb blue used throughout the app */
.btn-primary {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
