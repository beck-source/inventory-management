<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
      </div>
      <input
        type="range"
        min="0"
        max="100000"
        step="500"
        v-model.number="budget"
        class="budget-slider"
      />
      <div class="budget-range-labels">
        <span>{{ formatCurrency(0, currentCurrency) }}</span>
        <span>{{ formatCurrency(100000, currentCurrency) }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.recommendedCount') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost, currentCurrency) }}</div>
        </div>
        <div class="stat-card" :class="remainingBudget < 0 ? 'danger' : 'warning'">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(remainingBudget, currentCurrency) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="loading">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td><span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span></td>
                <td>{{ item.forecasted_demand }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td><strong>{{ formatCurrency(item.line_total, currentCurrency) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="place-order-row">
          <div v-if="orderConfirmation" class="order-success">
            {{ t('restocking.orderPlaced', { orderNumber: orderConfirmation.order_number }) }}
          </div>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placing || !!orderConfirmation"
            @click="placeOrder"
          >
            {{ placing ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(20000)
    const recommendations = ref([])
    const placing = ref(false)
    const orderConfirmation = ref(null)

    // Use shared filters (warehouse/category only — budget is local to this view)
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const totalCost = computed(() => recommendations.value.reduce((sum, item) => sum + item.line_total, 0))
    const remainingBudget = computed(() => budget.value - totalCost.value)

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        recommendations.value = await api.getRestockRecommendations(budget.value, {
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce so dragging the slider doesn't fire a request per pixel
    let debounceTimer = null
    const scheduleLoad = () => {
      orderConfirmation.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 250)
    }

    watch([budget, selectedLocation, selectedCategory], scheduleLoad)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      try {
        placing.value = true
        error.value = null
        const payload = {
          items: recommendations.value.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost
          })),
          budget: budget.value
        }
        orderConfirmation.value = await api.createRestockOrder(payload)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currentCurrency,
      formatCurrency,
      loading,
      error,
      budget,
      recommendations,
      totalCost,
      remainingBudget,
      placing,
      orderConfirmation,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding-bottom: 1.5rem;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  margin: 0.5rem 0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}

.budget-slider:focus {
  outline: none;
}

.budget-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.order-success {
  flex: 1;
  background: #d1fae5;
  color: #065f46;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
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
  transition: background 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
