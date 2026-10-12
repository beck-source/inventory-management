<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Configuration Card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3>{{ t('restocking.budgetConfiguration') }}</h3>
        </div>
        <div class="budget-controls">
          <div class="budget-display">
            <label>{{ t('restocking.availableBudget') }}</label>
            <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
          </div>
          <div class="budget-slider-container">
            <input
              type="range"
              v-model.number="budget"
              :min="1000"
              :max="50000"
              :step="500"
              class="budget-slider"
            />
            <div class="slider-labels">
              <span>{{ currencySymbol }}1,000</span>
              <span>{{ currencySymbol }}50,000</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card recommendations-card">
        <div class="card-header">
          <h3>{{ t('restocking.recommendations') }}</h3>
          <div class="summary-badge">
            {{ recommendations.length }} {{ t('restocking.items') }} •
            {{ currencySymbol }}{{ totalCost.toLocaleString() }} /
            {{ currencySymbol }}{{ budget.toLocaleString() }}
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          <p>{{ t('restocking.noRecommendations') }}</p>
        </div>

        <div v-else class="recommendations-list">
          <div class="table-container">
            <table class="recommendations-table">
              <thead>
                <tr>
                  <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                  <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                  <th class="col-stock">{{ t('restocking.table.currentStock') }}</th>
                  <th class="col-stock">{{ t('restocking.table.reorderPoint') }}</th>
                  <th class="col-stock">{{ t('restocking.table.forecastedDemand') }}</th>
                  <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                  <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                  <th class="col-cost">{{ t('restocking.table.subtotal') }}</th>
                  <th class="col-priority">{{ t('restocking.table.priority') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.sku">
                  <td class="col-sku"><strong>{{ item.sku }}</strong></td>
                  <td class="col-name">{{ translateProductName(item.name) }}</td>
                  <td class="col-stock">
                    <span class="stock-critical">{{ item.quantity_on_hand }}</span>
                  </td>
                  <td class="col-stock">{{ item.reorder_point }}</td>
                  <td class="col-stock">{{ item.forecastedDemand || '-' }}</td>
                  <td class="col-qty"><strong>{{ item.recommendedQuantity }}</strong></td>
                  <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                  <td class="col-cost"><strong>{{ currencySymbol }}{{ item.subtotal.toLocaleString() }}</strong></td>
                  <td class="col-priority">
                    <span :class="['badge', getPriorityClass(item.priorityScore)]">
                      {{ getPriorityLabel(item.priorityScore) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="card-actions">
          <button
            @click="placeOrder"
            :disabled="recommendations.length === 0 || submitting"
            class="btn btn-primary"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="orderSuccess" class="success-message">
        <p>{{ t('restocking.orderSuccess', { orderNumber: successOrderNumber }) }}</p>
        <router-link to="/orders" class="btn btn-link">
          {{ t('restocking.viewOrders') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const router = useRouter()
    const { t, currentCurrency, translateProductName } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const BUDGET_STORAGE_KEY = 'restocking-budget'

    // State
    const budget = ref(Number(localStorage.getItem(BUDGET_STORAGE_KEY)) || 5000)
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const inventoryItems = ref([])
    const demandForecasts = ref([])
    const recommendations = ref([])
    const orderSuccess = ref(false)
    const successOrderNumber = ref('')

    // Computed
    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.subtotal, 0)
    })

    // Load data from API
    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        const filters = getCurrentFilters()
        const [inventory, forecasts] = await Promise.all([
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          }),
          api.getDemandForecasts()
        ])

        inventoryItems.value = inventory
        demandForecasts.value = forecasts

        calculateRecommendations()
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Calculate recommendations based on low stock and budget
    const calculateRecommendations = () => {
      // Find items below reorder point (low stock)
      const candidates = inventoryItems.value
        .filter(item => item.quantity_on_hand <= item.reorder_point)
        .map(item => {
          // Calculate priority: 70% stock urgency + 30% demand factor
          const stockUrgency = Math.max(0,
            (item.reorder_point - item.quantity_on_hand) / item.reorder_point
          )

          // Match with demand forecast by SKU
          const forecast = demandForecasts.value.find(f => f.item_sku === item.sku)
          const demandFactor = forecast ?
            Math.min(forecast.forecasted_demand / 1000, 1.0) : 0

          const priorityScore = (stockUrgency * 0.7) + (demandFactor * 0.3)

          return {
            ...item,
            priorityScore,
            forecastedDemand: forecast?.forecasted_demand || 0
          }
        })
        .sort((a, b) => b.priorityScore - a.priorityScore)

      // Allocate budget greedily
      const result = []
      let remainingBudget = budget.value

      for (const item of candidates) {
        const quantityNeeded = item.reorder_point - item.quantity_on_hand
        const itemCost = quantityNeeded * item.unit_cost

        if (itemCost <= remainingBudget) {
          // Full order
          result.push({
            ...item,
            recommendedQuantity: quantityNeeded,
            subtotal: itemCost
          })
          remainingBudget -= itemCost
        } else {
          // Partial order
          const affordableQty = Math.floor(remainingBudget / item.unit_cost)
          if (affordableQty > 0) {
            result.push({
              ...item,
              recommendedQuantity: affordableQty,
              subtotal: affordableQty * item.unit_cost
            })
            remainingBudget -= (affordableQty * item.unit_cost)
          }
          break // Budget exhausted
        }
      }

      recommendations.value = result
    }

    // Place restocking order
    const placeOrder = async () => {
      try {
        submitting.value = true

        const orderData = {
          budget: budget.value,
          items: recommendations.value.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.recommendedQuantity,
            unit_cost: item.unit_cost,
            reorder_point: item.reorder_point,
            current_stock: item.quantity_on_hand,
            forecasted_demand: item.forecastedDemand,
            priority_score: item.priorityScore
          })),
          total_cost: totalCost.value,
          warehouse: getCurrentFilters().warehouse
        }

        const response = await api.createRestockingOrder(orderData)

        successOrderNumber.value = response.order_number
        orderSuccess.value = true

        // Redirect after 2 seconds
        setTimeout(() => {
          router.push('/orders')
        }, 2000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const getPriorityClass = (score) => {
      if (score >= 0.7) return 'danger'
      if (score >= 0.4) return 'warning'
      return 'info'
    }

    const getPriorityLabel = (score) => {
      if (score >= 0.7) return t('priority.high')
      if (score >= 0.4) return t('priority.medium')
      return t('priority.low')
    }

    // Watch for budget changes and save to localStorage
    watch(budget, (newBudget) => {
      localStorage.setItem(BUDGET_STORAGE_KEY, newBudget.toString())
      calculateRecommendations()
    })

    // Watch for filter changes
    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      budget,
      loading,
      error,
      submitting,
      recommendations,
      totalCost,
      currencySymbol,
      orderSuccess,
      successOrderNumber,
      placeOrder,
      getPriorityClass,
      getPriorityLabel,
      translateProductName
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 1rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  color: #0f172a;
  font-size: 1.875rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  color: #0f172a;
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.summary-badge {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.813rem;
  color: #475569;
}

.budget-card {
  margin-top: 1.5rem;
}

.budget-controls {
  padding: 1.5rem;
}

.budget-display {
  margin-bottom: 1.5rem;
}

.budget-display label {
  display: block;
  color: #475569;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2563eb;
}

.budget-slider-container {
  margin-bottom: 0.5rem;
}

.budget-slider {
  width: 100%;
  height: 0.5rem;
  cursor: pointer;
  background: #e2e8f0;
  border-radius: 0.25rem;
  appearance: none;
  -webkit-appearance: none;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.budget-slider::-moz-range-thumb {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 0.813rem;
  margin-top: 0.5rem;
}

.recommendations-list {
  padding: 0;
  overflow-x: auto;
}

.table-container {
  overflow-x: auto;
}

.recommendations-table {
  width: 100%;
  border-collapse: collapse;
}

.recommendations-table thead {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}

.recommendations-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 0.813rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.recommendations-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
  font-size: 0.938rem;
}

.col-sku { width: 80px; }
.col-name { min-width: 180px; }
.col-stock { width: 100px; }
.col-qty { width: 90px; text-align: center; }
.col-cost { width: 100px; text-align: right; }
.col-priority { width: 80px; text-align: center; }

.stock-critical {
  color: #dc2626;
  font-weight: 600;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.card-actions {
  padding: 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
}

.btn {
  padding: 0.625rem 1.5rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.btn-link {
  background: transparent;
  color: #2563eb;
  padding: 0;
  text-decoration: none;
  padding: 0.5rem;
}

.btn-link:hover {
  text-decoration: underline;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #64748b;
}

.error {
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 0.375rem;
  padding: 1rem;
  color: #991b1b;
  margin-bottom: 1rem;
}

.success-message {
  background: #dcfce7;
  border: 1px solid #bbf7d0;
  border-radius: 0.375rem;
  padding: 1rem;
  color: #15803d;
  text-align: center;
  margin-top: 1rem;
}

.success-message p {
  margin-bottom: 0.75rem;
  font-weight: 600;
}
</style>
