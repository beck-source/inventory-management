<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading && !recommendations" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-container">
          <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
          <input
            type="range"
            min="0"
            max="50000"
            step="500"
            v-model.number="budget"
            class="budget-slider"
          />
        </div>
      </div>

      <div v-if="orderConfirmation" class="confirmation-banner">
        <h3>{{ t('restocking.confirmationTitle') }}</h3>
        <p>
          {{ t('restocking.confirmationMessage', {
            orderNumber: orderConfirmation.order_number,
            days: orderConfirmation.lead_time_days
          }) }}
        </p>
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
          <button
            class="place-order-btn"
            :disabled="!recommendations || recommendations.items.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="!recommendations || recommendations.items.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.name') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th>{{ t('restocking.table.percentIncrease') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations.items" :key="item.sku">
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ item.name }}</td>
                  <td>
                    <span :class="['badge', item.trend]">
                      {{ t(`trends.${item.trend}`) }}
                    </span>
                  </td>
                  <td>{{ item.percent_increase }}%</td>
                  <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                  <td>{{ item.recommended_qty }}</td>
                  <td><strong>{{ formatCurrency(item.line_total, currentCurrency) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="summary-strip">
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.totalCost') }}</span>
              <span class="summary-value">{{ formatCurrency(recommendations.total_cost, currentCurrency) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.remainingBudget') }}</span>
              <span class="summary-value">{{ formatCurrency(recommendations.remaining_budget, currentCurrency) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const budget = ref(5000)
    const recommendations = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const orderConfirmation = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    const placeOrder = async () => {
      if (!recommendations.value || recommendations.value.items.length === 0) return
      submitting.value = true
      try {
        const items = recommendations.value.items.map(i => ({
          sku: i.sku,
          name: i.name,
          quantity: i.recommended_qty,
          unit_cost: i.unit_cost
        }))
        const order = await api.submitRestockOrder(budget.value, items)
        orderConfirmation.value = order
      } catch (err) {
        error.value = 'Failed to submit restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => {
      loadRecommendations()
    })

    return {
      t,
      currentCurrency,
      budget,
      recommendations,
      loading,
      error,
      submitting,
      orderConfirmation,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-progress {
  background: #3b82f6;
  height: 6px;
  border-radius: 3px;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

.summary-strip {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.confirmation-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1.25rem;
  border-radius: 10px;
  margin-bottom: 1.25rem;
}

.confirmation-banner h3 {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 0.375rem;
}

.confirmation-banner p {
  font-size: 0.938rem;
  margin-bottom: 0.5rem;
}

.confirmation-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}
</style>
