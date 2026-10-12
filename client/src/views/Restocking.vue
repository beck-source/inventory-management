<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-display">{{ formatCurrency(budget) }}</div>
      <input
        type="range"
        min="0"
        max="65000"
        step="500"
        v-model.number="budget"
        class="slider"
      />
      <div class="budget-stats">
        <div class="budget-stat">
          <span class="budget-stat-label">{{ t('restocking.totalCost') }}</span>
          <span class="budget-stat-value">{{ formatCurrency(recommendations.total_cost) }}</span>
        </div>
        <div class="budget-stat">
          <span class="budget-stat-label">{{ t('restocking.remainingBudget') }}</span>
          <span class="budget-stat-value">{{ formatCurrency(recommendations.remaining_budget) }}</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="budget > 0">
        <div v-if="recommendations.items.length > 0" class="card">
          <div class="card-header">
            <h3 class="card-title">
              {{ t('restocking.recommendations') }} ({{ t('restocking.itemsCount', { count: recommendations.items.length }) }})
            </h3>
            <button
              class="place-order-btn"
              :disabled="recommendations.items.length === 0 || orderSubmitted"
              @click="placeOrder"
            >
              {{ t('restocking.placeOrder') }}
            </button>
          </div>

          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th>{{ t('restocking.table.forecastedQty') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.totalCost') }}</th>
                  <th>{{ t('restocking.table.leadTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations.items" :key="item.item_sku">
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ item.item_name }}</td>
                  <td>
                    <span :class="['badge', item.trend.toLowerCase()]">{{ item.trend }}</span>
                  </td>
                  <td>{{ item.forecasted_demand }}</td>
                  <td>{{ formatCurrency(item.unit_cost) }}</td>
                  <td>{{ formatCurrency(item.total_cost) }}</td>
                  <td>{{ item.lead_time_days }} {{ t('restocking.table.days') }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="totals-row">
                  <td colspan="5"><strong>{{ t('restocking.totalCost') }}</strong></td>
                  <td><strong>{{ formatCurrency(recommendations.total_cost) }}</strong></td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div v-else class="card">
          <p class="empty-state">{{ t('restocking.noRecommendations') }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const budget = ref(10000)
    const maxBudget = 65000
    const recommendations = ref({ items: [], total_cost: 0, remaining_budget: 0 })
    const loading = ref(false)
    const error = ref(null)
    const orderSubmitted = ref(false)
    const successMessage = ref('')

    const fetchRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    let debounceTimer = null
    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        orderSubmitted.value = false
        fetchRecommendations()
      }, 300)
    })

    const placeOrder = async () => {
      try {
        await api.submitRestockingOrder(recommendations.value.items)
        orderSubmitted.value = true
        successMessage.value = t('restocking.orderPlaced')
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      }
    }

    const formatCurrency = (value) => {
      return '$' + Number(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    onMounted(fetchRecommendations)

    return {
      t,
      budget,
      maxBudget,
      recommendations,
      loading,
      error,
      orderSubmitted,
      successMessage,
      placeOrder,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.slider {
  width: 100%;
  accent-color: #3b82f6;
  height: 6px;
  cursor: pointer;
  margin-bottom: 1rem;
}

.budget-stats {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.budget-stat-value {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
}

.success-message {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.totals-row td {
  background: #f8fafc;
  border-top: 2px solid #e2e8f0;
  font-weight: 700;
  color: #0f172a;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem;
  font-size: 0.938rem;
}
</style>
