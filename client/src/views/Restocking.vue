<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Control Section -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.setBudget') }}</h3>
      </div>
      <div class="budget-controls">
        <div class="budget-input-group">
          <label for="budget-number">{{ t('restocking.availableBudget') }}</label>
          <div class="currency-input">
            <span class="currency-symbol">{{ currencySymbol }}</span>
            <input
              id="budget-number"
              type="number"
              v-model.number="budgetAmount"
              @input="updateBudget"
              min="0"
              max="500000"
              step="1000"
              class="budget-number-input"
            />
          </div>
        </div>
        <div class="budget-slider-group">
          <input
            type="range"
            v-model.number="budgetAmount"
            @input="debouncedUpdateBudget"
            min="0"
            max="500000"
            step="1000"
            class="budget-slider"
          />
          <div class="slider-labels">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}500K</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Summary Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.items_count || 0 }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendations.total_cost || 0).toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendations.remaining_budget || 0).toLocaleString() }}</div>
        </div>
      </div>

      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.items_count || 0 }})</h3>
          <button
            @click="submitOrder"
            :disabled="selectedItems.length === 0 || submitting"
            class="place-order-btn"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder', { count: selectedItems.length }) }}
          </button>
        </div>

        <div v-if="!recommendations.recommendations || recommendations.recommendations.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="col-checkbox">
                  <input
                    type="checkbox"
                    @change="toggleSelectAll"
                    :checked="selectedItems.length === recommendations.recommendations.length"
                    class="select-all-checkbox"
                  />
                </th>
                <th class="col-priority">{{ t('restocking.table.priority') }}</th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-category">{{ t('restocking.table.category') }}</th>
                <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                <th class="col-stock">{{ t('restocking.table.currentStock') }}</th>
                <th class="col-reorder">{{ t('restocking.table.reorderPoint') }}</th>
                <th class="col-demand">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-total">{{ t('restocking.table.totalCost') }}</th>
                <th class="col-lead">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations.recommendations"
                :key="item.item_sku"
                :class="{ 'selected-row': isSelected(item.item_sku) }"
              >
                <td class="col-checkbox">
                  <input
                    type="checkbox"
                    :checked="isSelected(item.item_sku)"
                    @change="toggleItem(item.item_sku)"
                    class="item-checkbox"
                  />
                </td>
                <td class="col-priority">
                  <span :class="['priority-badge', getPriorityClass(item.priority_score)]">
                    {{ item.priority_score }}
                  </span>
                </td>
                <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-category">{{ item.category }}</td>
                <td class="col-warehouse">{{ item.warehouse }}</td>
                <td class="col-stock" :class="{ 'low-stock': item.current_stock <= item.reorder_point }">
                  {{ item.current_stock }}
                </td>
                <td class="col-reorder">{{ item.reorder_point }}</td>
                <td class="col-demand" :class="{ 'high-demand': item.forecasted_demand > item.current_stock }">
                  {{ item.forecasted_demand }}
                </td>
                <td class="col-qty"><strong>{{ item.recommended_quantity }}</strong></td>
                <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td class="col-total"><strong>{{ currencySymbol }}{{ (item.recommended_quantity * item.unit_cost).toLocaleString() }}</strong></td>
                <td class="col-lead">{{ item.lead_time_days }} {{ t('restocking.days') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const router = useRouter()
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Reactive state
    const budgetAmount = ref(100000)
    const recommendations = ref({})
    const selectedItems = ref([])
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)

    // Debounce timer
    let debounceTimer = null

    // Load recommendations from API
    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const data = await api.getRestockingRecommendations(budgetAmount.value, filters)
        recommendations.value = data

        // Auto-select all recommendations by default
        selectedItems.value = (data.recommendations || []).map(item => item.item_sku)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error('Load recommendations error:', err)
      } finally {
        loading.value = false
      }
    }

    // Immediate update for number input
    const updateBudget = () => {
      loadRecommendations()
    }

    // Debounced update for slider
    const debouncedUpdateBudget = () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 500)
    }

    // Toggle select all checkbox
    const toggleSelectAll = (event) => {
      if (event.target.checked) {
        selectedItems.value = (recommendations.value.recommendations || []).map(item => item.item_sku)
      } else {
        selectedItems.value = []
      }
    }

    // Toggle individual item selection
    const toggleItem = (sku) => {
      const index = selectedItems.value.indexOf(sku)
      if (index > -1) {
        selectedItems.value.splice(index, 1)
      } else {
        selectedItems.value.push(sku)
      }
    }

    // Check if item is selected
    const isSelected = (sku) => {
      return selectedItems.value.includes(sku)
    }

    // Get priority class based on score
    const getPriorityClass = (score) => {
      if (score >= 100) return 'high'
      if (score >= 50) return 'medium'
      return 'low'
    }

    // Submit restocking order
    const submitOrder = async () => {
      if (selectedItems.value.length === 0) return

      try {
        submitting.value = true

        // Filter recommendations to only include selected items
        const selectedRecommendations = (recommendations.value.recommendations || [])
          .filter(item => isSelected(item.item_sku))
          .map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            category: item.category,
            warehouse: item.warehouse,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost
          }))

        await api.submitRestockingOrder({
          budget: budgetAmount.value,
          recommendations: selectedRecommendations
        })

        // Redirect to Orders tab on success
        router.push('/orders')
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
        console.error('Submit order error:', err)
      } finally {
        submitting.value = false
      }
    }

    // Watch for filter changes and reload recommendations
    watch([selectedLocation, selectedCategory], () => {
      loadRecommendations()
    })

    onMounted(() => {
      loadRecommendations()
    })

    return {
      t,
      currencySymbol,
      budgetAmount,
      recommendations,
      selectedItems,
      loading,
      error,
      submitting,
      updateBudget,
      debouncedUpdateBudget,
      toggleSelectAll,
      toggleItem,
      isSelected,
      getPriorityClass,
      submitOrder
    }
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
  margin: 0;
}

/* Budget Card */
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-controls {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.budget-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-input-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.currency-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.currency-symbol {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-number-input {
  flex: 1;
  max-width: 300px;
  padding: 0.75rem 1rem;
  font-size: 1.25rem;
  font-weight: 600;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  transition: border-color 0.2s ease;
}

.budget-number-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.budget-slider-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  transition: all 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-card.info {
  border-left: 4px solid #3b82f6;
}

.stat-card.success {
  border-left: 4px solid #10b981;
}

.stat-card.warning {
  border-left: 4px solid #f59e0b;
}

.stat-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

/* Table Styles */
.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-checkbox {
  width: 50px;
  text-align: center;
}

.col-priority {
  width: 80px;
  text-align: center;
}

.col-sku {
  width: 100px;
}

.col-name {
  width: 180px;
}

.col-category {
  width: 120px;
}

.col-warehouse {
  width: 140px;
}

.col-stock {
  width: 90px;
  text-align: right;
}

.col-reorder {
  width: 100px;
  text-align: right;
}

.col-demand {
  width: 110px;
  text-align: right;
}

.col-qty {
  width: 100px;
  text-align: right;
}

.col-cost {
  width: 100px;
  text-align: right;
}

.col-total {
  width: 120px;
  text-align: right;
}

.col-lead {
  width: 90px;
  text-align: center;
}

.select-all-checkbox,
.item-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #3b82f6;
}

.priority-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  text-align: center;
  min-width: 50px;
}

.priority-badge.high {
  background: #fee2e2;
  color: #ef4444;
}

.priority-badge.medium {
  background: #fed7aa;
  color: #f97316;
}

.priority-badge.low {
  background: #dbeafe;
  color: #3b82f6;
}

.low-stock {
  color: #ef4444;
  font-weight: 600;
}

.high-demand {
  color: #10b981;
  font-weight: 600;
}

.selected-row {
  background: #f0f9ff;
}

.place-order-btn {
  padding: 0.625rem 1.25rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  transform: none;
}

.no-recommendations {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 1rem;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .budget-number-input {
    max-width: none;
  }
}
</style>
