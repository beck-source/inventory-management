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
        <div class="budget-header">
          <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
          <span class="budget-value">{{ formattedBudget }}</span>
        </div>
        <input
          id="budget-slider"
          type="range"
          class="budget-slider"
          v-model.number="budget"
          :min="0"
          :max="sliderMax"
          step="50"
          @change="loadRecommendations"
        >
        <div class="budget-max-hint">
          {{ t('restocking.maxPossibleCost') }}: {{ formattedMaxPossibleCost }}
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.budget') }}</div>
          <div class="stat-value">{{ formattedBudget }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.stats.itemsFunded') }}</div>
          <div class="stat-value">{{ itemsFundedCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.totalCost') }}</div>
          <div class="stat-value">{{ formattedTotalCost }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.stats.remainingBudget') }}</div>
          <div class="stat-value">{{ formattedRemainingBudget }}</div>
        </div>
      </div>

      <div v-if="orderSuccessResult" class="order-success-banner">
        <div>
          <strong>{{ t('restocking.orderSuccess') }}</strong>
          <span> {{ t('restocking.orderSuccessDetail') }}</span>
        </div>
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <div v-if="orderError" class="error">{{ orderError }}</div>
      <div v-if="refreshError" class="error">{{ refreshError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
          <span v-if="refreshing" class="refreshing-hint">{{ t('common.loading') }}</span>
        </div>
        <div class="table-container" :class="{ 'is-refreshing': refreshing }">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.recommendedQuantity') }}</th>
                <th>{{ t('restocking.table.quantityIncluded') }}</th>
                <th>{{ t('restocking.table.subtotal') }}</th>
                <th>{{ t('restocking.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td>{{ item.item_name }}</td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ item.quantity_included }}</td>
                <td>{{ formatCurrency(item.subtotal) }}</td>
                <td>
                  <span :class="['badge', getFundedStatusClass(item)]">
                    {{ t(getFundedStatusKey(item)) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="place-order-row">
          <button
            class="btn-primary"
            :disabled="totalCost === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
          <span v-if="totalCost === 0" class="no-items-hint">
            {{ t('restocking.noItemsFunded') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    // `loading` only gates the very first load (full-page loading state).
    // Subsequent slider-triggered reloads use `refreshing` instead, so the
    // slider and already-loaded content stay visible while data refreshes.
    const loading = ref(true)
    const error = ref(null)
    const refreshing = ref(false)
    const refreshError = ref(null)
    const hasLoadedOnce = ref(false)

    const budget = ref(1000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const maxPossibleCost = ref(0)

    const submitting = ref(false)
    const orderError = ref(null)
    const orderSuccessResult = ref(null)

    const sliderMax = computed(() => {
      return Math.max(Math.ceil(maxPossibleCost.value / 100) * 100, 1000)
    })

    const itemsFundedCount = computed(() => {
      return recommendations.value.filter(item => item.quantity_included > 0).length
    })

    const formatCurrency = (value) => {
      return formatCurrencyWithDecimals(value || 0, currentCurrency.value, 2)
    }

    const formattedBudget = computed(() => formatCurrency(budget.value))
    const formattedTotalCost = computed(() => formatCurrency(totalCost.value))
    const formattedRemainingBudget = computed(() => formatCurrency(remainingBudget.value))
    const formattedMaxPossibleCost = computed(() => formatCurrency(maxPossibleCost.value))

    const getFundedStatusClass = (item) => {
      if (item.fully_funded) return 'success'
      if (item.quantity_included > 0) return 'warning'
      return 'muted'
    }

    const getFundedStatusKey = (item) => {
      if (item.fully_funded) return 'restocking.fundedStatus.fullyFunded'
      if (item.quantity_included > 0) return 'restocking.fundedStatus.partiallyFunded'
      return 'restocking.fundedStatus.notFunded'
    }

    const loadRecommendations = async () => {
      // A budget change while a previous success/error banner is showing
      // should clear it - it referred to the old budget.
      orderSuccessResult.value = null
      orderError.value = null

      if (!hasLoadedOnce.value) {
        loading.value = true
      } else {
        refreshing.value = true
      }
      error.value = null
      refreshError.value = null

      try {
        const response = await api.getRestockRecommendations(budget.value)
        recommendations.value = response.items
        totalCost.value = response.total_cost
        remainingBudget.value = response.remaining_budget
        maxPossibleCost.value = response.max_possible_cost
        hasLoadedOnce.value = true
      } catch (err) {
        if (!hasLoadedOnce.value) {
          error.value = 'Failed to load restock recommendations: ' + err.message
        } else {
          refreshError.value = 'Failed to refresh recommendations: ' + err.message
        }
      } finally {
        loading.value = false
        refreshing.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      orderError.value = null
      orderSuccessResult.value = null
      try {
        const result = await api.submitRestockOrder(budget.value)
        orderSuccessResult.value = result
      } catch (err) {
        const detail = err.response?.data?.detail
        orderError.value = detail
          ? `${t('restocking.orderError')}: ${detail}`
          : t('restocking.orderError')
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadRecommendations())

    return {
      t,
      loading,
      error,
      refreshing,
      refreshError,
      budget,
      sliderMax,
      recommendations,
      totalCost,
      remainingBudget,
      maxPossibleCost,
      itemsFundedCount,
      formattedBudget,
      formattedTotalCost,
      formattedRemainingBudget,
      formattedMaxPossibleCost,
      formatCurrency,
      getFundedStatusClass,
      getFundedStatusKey,
      loadRecommendations,
      submitting,
      orderError,
      orderSuccessResult,
      placeOrder
    }
  }
}
</script>

<style scoped>
.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.muted {
  background: #f1f5f9;
  color: #64748b;
}

.budget-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  cursor: pointer;
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
}

.budget-max-hint {
  font-size: 0.813rem;
  color: #64748b;
}

.order-success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.order-success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.place-order-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.no-items-hint {
  font-size: 0.875rem;
  color: #64748b;
}

.refreshing-hint {
  font-size: 0.813rem;
  color: #64748b;
}

.table-container.is-refreshing {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}
</style>
