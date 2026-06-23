<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-controls">
        <label class="budget-label" for="budget-slider">
          {{ t('restocking.budgetLabel') }}: <strong>{{ formattedBudget }}</strong>
        </label>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="500"
          max="50000"
          step="500"
          class="budget-slider"
          @change="loadRecommendations"
        >
        <button class="btn-primary" :disabled="loading" @click="loadRecommendations">
          {{ t('restocking.getRecommendations') }}
        </button>
      </div>
    </div>

    <div v-if="successMessage" class="success-banner">
      <span>{{ successMessage }}</span>
      <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.totalBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(summary.total_budget) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.totalAllocated') }}</div>
          <div class="stat-value">{{ formatCurrency(summary.total_allocated) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(summary.remaining_budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.itemCount') }}</div>
          <div class="stat-value">{{ summary.item_count }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
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
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.suggestedQuantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.warehouse }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.current_demand }}</td>
                <td><strong>{{ item.forecasted_demand }}</strong></td>
                <td>{{ item.suggested_quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ formatCurrency(item.total_cost) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="place-order-row">
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
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyValue } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const budget = ref(5000)
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)

    const recommendations = ref([])
    const summary = ref({
      total_budget: 0,
      total_allocated: 0,
      remaining_budget: 0,
      item_count: 0
    })

    // Format the current budget slider value as a currency string.
    const formattedBudget = computed(() => formatCurrencyValue(budget.value, currentCurrency.value))

    // Format a numeric amount as a currency string using the active locale's currency.
    const formatCurrency = (amount) => formatCurrencyValue(amount || 0, currentCurrency.value)

    // Load restocking recommendations for the current budget value.
    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        successMessage.value = null
        const response = await api.getRestockingRecommendations(budget.value)
        recommendations.value = response.recommendations
        summary.value = {
          total_budget: response.total_budget,
          total_allocated: response.total_allocated,
          remaining_budget: response.remaining_budget,
          item_count: response.item_count
        }
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Submit the current recommendations as a new restocking order.
    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        const items = recommendations.value.map((item) => ({
          sku: item.sku,
          item_name: item.item_name,
          quantity: item.suggested_quantity,
          unit_cost: item.unit_cost,
          warehouse: item.warehouse,
          category: item.category
        }))
        await api.createRestockingOrder({ items })
        successMessage.value = t('restocking.success')
        recommendations.value = []
      } catch (err) {
        error.value = 'Failed to place restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadRecommendations())

    return {
      t,
      budget,
      loading,
      error,
      submitting,
      successMessage,
      recommendations,
      summary,
      formattedBudget,
      formatCurrency,
      loadRecommendations,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  align-items: center;
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
  flex-wrap: wrap;
}

.budget-label {
  font-size: 0.938rem;
  color: #334155;
  font-weight: 500;
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  min-width: 12rem;
  accent-color: #2563eb;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.938rem;
}

.success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
