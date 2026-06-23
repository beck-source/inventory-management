<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget control -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <div class="budget-readout">{{ formatCurrency(budget) }}</div>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          :step="sliderStep"
          v-model.number="budget"
        />
        <div class="slider-scale">
          <span>{{ formatCurrency(0) }}</span>
          <span>{{ formatCurrency(maxBudget) }}</span>
        </div>
        <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>
      </div>

      <!-- Summary -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.items') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(remaining) }}</div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.restockQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.id">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td><strong>{{ item.gap.toLocaleString() }}</strong></td>
                <td>{{ formatCurrency(item.unitCost) }}</td>
                <td>{{ formatCurrency(item.lineCost) }}</td>
                <td>{{ item.leadTimeDays }} {{ t('restocking.days') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Place order -->
      <div class="order-actions">
        <div v-if="successMessage" class="success-banner">
          {{ successMessage }}
          <router-link to="/orders" class="success-link">{{ t('nav.orders') }} →</router-link>
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>
        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

// Lead time (days) by demand trend — mirrors the backend's authoritative mapping so the
// table can preview delivery speed before the order is actually submitted.
const LEAD_TIME_BY_TREND = { increasing: 7, stable: 14, decreasing: 21 }
const DEFAULT_LEAD_TIME_DAYS = 14

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const successMessage = ref('')
    const submitError = ref('')

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))
    const formatCurrency = (n) => `${currencySymbol.value}${Math.round(n || 0).toLocaleString()}`

    // Candidate restock lines: only items whose forecast exceeds current demand (a real shortfall).
    // Restock quantity is the gap; line cost prices the gap at the forecast item's unit_cost.
    const candidates = computed(() => {
      return allForecasts.value
        .filter((f) => f.forecasted_demand > f.current_demand)
        .map((f) => {
          const gap = f.forecasted_demand - f.current_demand
          return {
            id: f.id,
            sku: f.item_sku,
            name: f.item_name,
            trend: f.trend,
            gap,
            unitCost: f.unit_cost,
            lineCost: gap * f.unit_cost,
            leadTimeDays: LEAD_TIME_BY_TREND[f.trend] ?? DEFAULT_LEAD_TIME_DAYS
          }
        })
        .sort((a, b) => b.gap - a.gap) // biggest shortfall first
    })

    // Full cost to cover every shortfall — used as the slider's upper bound.
    const maxBudget = computed(() =>
      Math.ceil(candidates.value.reduce((sum, c) => sum + c.lineCost, 0))
    )

    // Round the slider step so dragging lands on tidy numbers regardless of total size.
    const sliderStep = computed(() => Math.max(100, Math.round(maxBudget.value / 100)))

    // Greedy fit: walk candidates (biggest shortfall first) and take each whole line that
    // still fits the remaining budget. Whole lines only — no partial quantities.
    const recommendations = computed(() => {
      const picked = []
      let spent = 0
      for (const c of candidates.value) {
        if (spent + c.lineCost <= budget.value) {
          picked.push(c)
          spent += c.lineCost
        }
      }
      return picked
    })

    const totalCost = computed(() => recommendations.value.reduce((sum, r) => sum + r.lineCost, 0))
    const remaining = computed(() => budget.value - totalCost.value)

    const loadForecasts = async () => {
      try {
        loading.value = true
        allForecasts.value = await api.getDemandForecasts()
        // Start at half the full-coverage cost so the page opens with a meaningful recommendation.
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      try {
        submitting.value = true
        submitError.value = ''
        successMessage.value = ''
        const payload = {
          budget: budget.value,
          items: recommendations.value.map((r) => ({
            sku: r.sku,
            name: r.name,
            quantity: r.gap,
            unit_price: r.unitCost,
            trend: r.trend
          }))
        }
        const order = await api.submitRestockOrder(payload)
        successMessage.value = t('restocking.successMessage', { orderNumber: order.order_number })
      } catch (err) {
        submitError.value = t('restocking.errorMessage', { error: err.message })
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      sliderStep,
      recommendations,
      totalCost,
      remaining,
      submitting,
      successMessage,
      submitError,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-readout {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  margin: 0.5rem 0 0.25rem;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.budget-help {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: #64748b;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.order-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  width: 100%;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.success-link {
  color: #047857;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.success-link:hover {
  text-decoration: underline;
}
</style>
