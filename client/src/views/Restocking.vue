<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-header">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        v-model.number="budget"
        type="range"
        min="1000"
        max="100000"
        step="500"
        class="budget-slider"
      />
      <div class="budget-bounds">
        <span>{{ currencySymbol }}{{ (1000).toLocaleString() }}</span>
        <span>{{ currencySymbol }}{{ (100000).toLocaleString() }}</span>
      </div>
    </div>

    <div v-if="successOrder" class="success-banner">
      <div class="success-text">
        <strong>{{ t('restocking.orderSuccess', { orderNumber: successOrder.order_number, date: formatDate(successOrder.expected_delivery) }) }}</strong>
        <span class="success-hint">{{ t('restocking.viewInOrders') }}</span>
      </div>
      <button class="dismiss-button" @click="successOrder = null">{{ t('restocking.dismiss') }}</button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="plan">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ plan.budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.plannedCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ plan.total_cost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ plan.remaining_budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsToRestock') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            class="place-order-button"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
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
                <th>{{ t('restocking.table.currentStock') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.estimatedCost') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ translateProductName(rec.item_name) }}</td>
                <td>{{ rec.current_stock.toLocaleString() }}</td>
                <td>{{ rec.forecasted_demand.toLocaleString() }}</td>
                <td>{{ rec.shortfall.toLocaleString() }}</td>
                <td>
                  <strong>{{ rec.recommended_quantity.toLocaleString() }}</strong>
                  <span v-if="rec.recommended_quantity < rec.shortfall" class="partial-hint">
                    {{ t('restocking.partialFill', { count: rec.shortfall.toLocaleString() }) }}
                  </span>
                </td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.estimated_cost.toLocaleString() }}</strong></td>
                <td>
                  <span :class="['badge', getTrendClass(rec.trend)]">
                    {{ t(`trends.${rec.trend}`) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(25000)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const plan = ref(null)
    const successOrder = ref(null)

    const recommendations = computed(() => {
      return plan.value ? plan.value.recommendations : []
    })

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        plan.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce budget changes so dragging the slider doesn't spam the backend
    let debounceTimer = null
    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    })

    onUnmounted(() => {
      clearTimeout(debounceTimer)
    })

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return
      try {
        submitting.value = true
        error.value = null
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(rec => ({
            item_sku: rec.item_sku,
            item_name: rec.item_name,
            quantity: rec.recommended_quantity,
            unit_cost: rec.unit_cost
          }))
        })
        successOrder.value = order
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const getTrendClass = (trend) => {
      const trendMap = {
        'increasing': 'success',
        'stable': 'info',
        'decreasing': 'warning'
      }
      return trendMap[trend] || 'info'
    }

    const formatDate = (dateString) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      budget,
      loading,
      error,
      submitting,
      plan,
      successOrder,
      recommendations,
      placeOrder,
      getTrendClass,
      formatDate,
      translateProductName
    }
  }
}
</script>

<style scoped>
/* Budget slider card */
.budget-card {
  padding: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
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
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
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
  background: #3b82f6;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.25);
  cursor: pointer;
  transition: background 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.25);
  cursor: pointer;
  transition: background 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
}

.budget-bounds {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

/* Success banner */
.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.success-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.success-hint {
  font-size: 0.875rem;
  color: #047857;
}

.dismiss-button {
  background: transparent;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.375rem 0.875rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s ease;
}

.dismiss-button:hover {
  background: #a7f3d0;
}

/* Place order button */
.place-order-button {
  background: #3b82f6;
  color: #ffffff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-button:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-button:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

/* Recommendations table */
.partial-hint {
  display: block;
  font-size: 0.75rem;
  color: #ea580c;
  margin-top: 0.125rem;
}

.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
