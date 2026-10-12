<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider Section -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.setBudget') }}</h3>
          <div class="budget-display">
            {{ currencySymbol }}{{ selectedBudget.toLocaleString() }}
          </div>
        </div>
        <div class="budget-slider-container">
          <div class="slider-labels">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
          </div>
          <input
            v-model.number="selectedBudget"
            type="range"
            min="0"
            :max="maxBudget"
            step="100"
            class="budget-slider"
          />
        </div>
      </div>

      <!-- Stats Cards Section -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ selectedBudget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsInRecommendations') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalEstimatedCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalEstimatedCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card" :class="{ 'budget-exceeded': budgetRemaining < 0 }">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">
            {{ currencySymbol }}{{ Math.abs(budgetRemaining).toLocaleString() }}
            <span v-if="budgetRemaining < 0" class="exceeded-indicator">{{ t('restocking.exceeded') }}</span>
          </div>
        </div>
      </div>

      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
        </div>
        <div v-if="recommendations.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.name') }}</th>
                <th class="col-stock">{{ t('restocking.table.currentStock') }}</th>
                <th class="col-demand">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-estimated">{{ t('restocking.table.estimatedCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td class="col-sku"><strong>{{ item.sku }}</strong></td>
                <td class="col-name">{{ item.name }}</td>
                <td class="col-stock">{{ item.current_stock }}</td>
                <td class="col-demand">{{ item.forecasted_demand }}</td>
                <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td class="col-qty">
                  <div class="qty-input-group">
                    <button
                      class="qty-btn"
                      @click="decreaseQty(item.sku)"
                      :disabled="itemQuantities[item.sku] <= 0"
                    >
                      −
                    </button>
                    <input
                      v-model.number="itemQuantities[item.sku]"
                      type="number"
                      min="0"
                      class="qty-input"
                      @change="validateQuantity(item.sku)"
                    />
                    <button
                      class="qty-btn"
                      @click="increaseQty(item.sku)"
                    >
                      +
                    </button>
                  </div>
                </td>
                <td class="col-estimated">{{ currencySymbol }}{{ getItemCost(item).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Place Order Section -->
      <div class="action-section">
        <button
          class="btn btn-primary"
          @click="submitOrder"
          :disabled="!canPlaceOrder"
        >
          {{ t('restocking.placeOrder') }}
        </button>
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
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

    const maxBudget = 50000
    const selectedBudget = ref(0)
    const loading = ref(true)
    const error = ref(null)
    const successMessage = ref(null)
    const recommendations = ref([])
    const itemQuantities = ref({})

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Calculate total estimated cost from all items
    const totalEstimatedCost = computed(() => {
      return recommendations.value.reduce((total, item) => {
        const qty = itemQuantities.value[item.sku] || 0
        return total + (qty * item.unit_cost)
      }, 0)
    })

    // Calculate budget remaining
    const budgetRemaining = computed(() => {
      return selectedBudget.value - totalEstimatedCost.value
    })

    // Can place order if budget is not exceeded and we have items
    const canPlaceOrder = computed(() => {
      return budgetRemaining.value >= 0 && totalEstimatedCost.value > 0
    })

    // Load initial data (forecasts and inventory)
    const loadInitialData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        // We'll use this data when recommendations are loaded
        // For now, just set initial budget to trigger recommendations load
        selectedBudget.value = 0
      } catch (err) {
        error.value = `${t('restocking.loadError')}: ${err.message}`
        console.error('Failed to load initial data:', err)
      } finally {
        loading.value = false
      }
    }

    // Load recommendations based on budget
    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(selectedBudget.value)
        recommendations.value = data

        // Initialize quantities to recommended amounts
        itemQuantities.value = {}
        data.forEach(item => {
          itemQuantities.value[item.sku] = item.recommended_qty || 0
        })
      } catch (err) {
        error.value = `${t('restocking.recommendationsError')}: ${err.message}`
        console.error('Failed to load recommendations:', err)
        recommendations.value = []
      } finally {
        loading.value = false
      }
    }

    // Watch budget slider changes
    watch(selectedBudget, () => {
      loadRecommendations()
      successMessage.value = null
    })

    // Get cost for a specific item
    const getItemCost = (item) => {
      const qty = itemQuantities.value[item.sku] || 0
      return qty * item.unit_cost
    }

    // Quantity adjustment helpers
    const increaseQty = (sku) => {
      if (itemQuantities.value[sku] === undefined) {
        itemQuantities.value[sku] = 0
      }
      itemQuantities.value[sku]++
    }

    const decreaseQty = (sku) => {
      if (itemQuantities.value[sku] && itemQuantities.value[sku] > 0) {
        itemQuantities.value[sku]--
      }
    }

    const validateQuantity = (sku) => {
      const qty = itemQuantities.value[sku]
      if (qty < 0 || isNaN(qty)) {
        itemQuantities.value[sku] = 0
      }
    }

    // Submit restocking order
    const submitOrder = async () => {
      try {
        // Build order data
        const items = recommendations.value
          .filter(item => (itemQuantities.value[item.sku] || 0) > 0)
          .map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: itemQuantities.value[item.sku],
            unit_cost: item.unit_cost
          }))

        if (items.length === 0) {
          error.value = t('restocking.noItemsSelected')
          return
        }

        const orderData = {
          items,
          total_cost: totalEstimatedCost.value,
          budget: selectedBudget.value
        }

        await api.submitRestockingOrder(orderData)

        // Show success message
        successMessage.value = t('restocking.orderSubmitted')

        // Reset form after 2 seconds
        setTimeout(() => {
          selectedBudget.value = 0
          itemQuantities.value = {}
          recommendations.value = []
          successMessage.value = null
        }, 2000)
      } catch (err) {
        error.value = `${t('restocking.submitError')}: ${err.message}`
        console.error('Failed to submit order:', err)
      }
    }

    onMounted(loadInitialData)

    return {
      t,
      loading,
      error,
      successMessage,
      selectedBudget,
      maxBudget,
      recommendations,
      itemQuantities,
      totalEstimatedCost,
      budgetRemaining,
      canPlaceOrder,
      currencySymbol,
      getItemCost,
      increaseQty,
      decreaseQty,
      validateQuantity,
      submitOrder
    }
  }
}
</script>

<style scoped>
/* Budget Card */
.budget-card {
  margin-bottom: 2rem;
}

.budget-display {
  font-size: 1.75rem;
  font-weight: 700;
  color: #3b82f6;
}

.budget-slider-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.5rem;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 5px;
  background: linear-gradient(to right, #e2e8f0 0%, #cbd5e1 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.budget-slider::-moz-range-thumb:hover {
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-card.budget-exceeded {
  background: #fef2f2;
  border-color: #fecaca;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.exceeded-indicator {
  font-size: 0.75rem;
  color: #ef4444;
  font-weight: 600;
  text-transform: uppercase;
  margin-left: 0.5rem;
}

/* Table Styling */
.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-sku {
  width: 100px;
}

.col-name {
  width: 180px;
}

.col-stock {
  width: 120px;
}

.col-demand {
  width: 140px;
}

.col-cost {
  width: 110px;
}

.col-qty {
  width: 140px;
}

.col-estimated {
  width: 120px;
}

/* Quantity Input Group */
.qty-input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  height: 36px;
}

.qty-btn {
  background: #f8fafc;
  border: none;
  padding: 0 0.75rem;
  cursor: pointer;
  font-size: 1.25rem;
  color: #64748b;
  transition: all 0.2s;
  height: 100%;
  flex: 0 0 auto;
}

.qty-btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}

.qty-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qty-input {
  flex: 1;
  border: none;
  outline: none;
  text-align: center;
  font-weight: 600;
  color: #0f172a;
  font-size: 0.875rem;
  background: transparent;
}

.qty-input::-webkit-outer-spin-button,
.qty-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.qty-input[type=number] {
  -moz-appearance: textfield;
}

/* No Data Message */
.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

/* Action Section */
.action-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-top: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  color: #059669;
  font-weight: 600;
  font-size: 0.875rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Global styles inherited from App.vue */
.loading,
.error {
  padding: 2rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.loading {
  background: #dbeafe;
  color: #1e40af;
  text-align: center;
}

.error {
  background: #fee2e2;
  color: #991b1b;
  text-align: center;
}

.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.card-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

thead tr {
  border-bottom: 2px solid #e2e8f0;
}

th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

td {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

tbody tr:hover {
  background: #f8fafc;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.5rem;
}

.page-header p {
  margin: 0;
  color: #64748b;
  font-size: 0.875rem;
}
</style>
