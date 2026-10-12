<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading && recommendations.length === 0" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <div class="budget-controls">
          <input
            id="budget-slider"
            type="range"
            class="budget-slider"
            min="0"
            max="50000"
            step="500"
            v-model.number="budget"
          />
          <span class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
      </div>

      <div v-if="orderSuccessMessage" class="success-banner">
        <span>{{ orderSuccessMessage }}</span>
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.totalBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ summary.budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.totalAllocated') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ summary.total_allocated.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.stats.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ summary.remaining_budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
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
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.gap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
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
                <td>{{ item.gap }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ item.lead_time_days }} {{ t('restocking.days') }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td><strong>{{ currencySymbol }}{{ item.estimated_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)
    const budget = ref(5000)
    const recommendations = ref([])
    const summary = ref({
      budget: 0,
      total_gap: 0,
      total_allocated: 0,
      remaining_budget: 0
    })
    const orderSuccessMessage = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations
        summary.value = {
          budget: data.budget,
          total_gap: data.total_gap,
          total_allocated: data.total_allocated,
          remaining_budget: data.remaining_budget
        }
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce budget-driven reloads so dragging the slider doesn't spam the API
    watch(budget, () => {
      orderSuccessMessage.value = null
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        orderSuccessMessage.value = null
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.recommended_quantity,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days
          }))
        })
        orderSuccessMessage.value = t('restocking.orderSuccess', { orderNumber: order.order_number })
      } catch (err) {
        error.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      loading,
      submitting,
      error,
      budget,
      recommendations,
      summary,
      currencySymbol,
      orderSuccessMessage,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #e2e8f0;
  accent-color: #3b82f6;
  outline: none;
  cursor: pointer;
}

.budget-slider:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.budget-readout {
  min-width: 100px;
  text-align: right;
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
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
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
