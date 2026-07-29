<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider">
          <input
            type="range"
            min="0"
            max="10000"
            step="100"
            v-model.number="budgetInput"
            @change="loadRecommendations"
            class="slider"
          />
          <span class="budget-value">${{ budgetInput.toLocaleString() }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.currentDemand') }}</th>
                  <th>{{ t('restocking.table.forecastedDemand') }}</th>
                  <th>{{ t('restocking.table.demandGap') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.recommendedQty') }}</th>
                  <th>{{ t('restocking.table.estimatedCost') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.item_sku">
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ item.item_name }}</td>
                  <td>{{ item.current_demand }}</td>
                  <td>{{ item.forecasted_demand }}</td>
                  <td>{{ item.demand_gap }}</td>
                  <td>${{ item.unit_cost.toLocaleString() }}</td>
                  <td>{{ item.recommended_quantity }}</td>
                  <td>${{ item.estimated_cost.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="summary-lines">
            <div class="summary-line">
              <span class="summary-label">{{ t('restocking.totalEstimatedCost') }}</span>
              <span class="summary-value">${{ totalEstimatedCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
            </div>
            <div class="summary-line">
              <span class="summary-label">{{ t('restocking.remainingBudget') }}</span>
              <span class="summary-value">${{ remainingBudget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
            </div>
          </div>
        </div>

        <div v-if="submitResult" class="success-banner">
          {{ t('restocking.orderSubmitted') }} - {{ submitResult.order_number }}
          ({{ t('restocking.leadTimeLabel') }}: {{ submitResult.lead_time_days }} {{ t('restocking.daysLabel') }})
        </div>

        <button
          class="place-order-btn"
          :disabled="submitting || recommendations.length === 0"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const budgetInput = ref(5000)
    const recommendations = ref([])
    const totalEstimatedCost = ref(0)
    const remainingBudget = ref(0)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitResult = ref(null)

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(budgetInput.value)
        recommendations.value = data.recommendations
        totalEstimatedCost.value = data.total_estimated_cost
        remainingBudget.value = data.remaining_budget
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        submitResult.value = null
        const orderData = {
          budget: budgetInput.value,
          items: recommendations.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.recommended_quantity,
            unit_cost: r.unit_cost
          }))
        }
        const result = await api.submitRestockOrder(orderData)
        submitResult.value = result
        // Re-fetch recommendations since budget usage may change on next reload
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to submit restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      budgetInput,
      recommendations,
      totalEstimatedCost,
      remainingBudget,
      loading,
      error,
      submitting,
      submitResult,
      loadRecommendations,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 6px;
  background: #e2e8f0;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: background 0.2s;
}

.slider::-webkit-slider-thumb:hover {
  background: #3b82f6;
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider::-moz-range-track {
  height: 6px;
  border-radius: 6px;
  background: #e2e8f0;
}

.slider:hover {
  background: #cbd5e1;
}

.budget-value {
  min-width: 100px;
  text-align: right;
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.summary-lines {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.summary-line {
  display: flex;
  justify-content: space-between;
  font-size: 0.938rem;
}

.summary-label {
  color: #64748b;
  font-weight: 500;
}

.summary-value {
  color: #0f172a;
  font-weight: 700;
}

.success-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}

.place-order-btn {
  margin-top: 1.25rem;
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
