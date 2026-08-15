<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Review AI-generated restocking recommendations and place orders based on your budget.</p>
    </div>

    <!-- Budget Slider Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Budget</h3>
        <span class="budget-label">{{ formattedBudget }}</span>
      </div>
      <div class="budget-slider-container">
        <span class="slider-bound">$1,000</span>
        <input
          type="range"
          class="budget-slider"
          min="1000"
          max="50000"
          step="1000"
          :value="budget"
          @input="onBudgetInput"
        />
        <span class="slider-bound">$50,000</span>
      </div>
    </div>

    <!-- Success State -->
    <div v-if="orderPlaced" class="card success-card">
      <div class="success-content">
        <div class="success-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="24" fill="#d1fae5"/>
            <path d="M14 24l8 8 12-16" stroke="#059669" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3 class="success-title">Order Placed Successfully</h3>
        <p class="success-message">
          Your restocking order for {{ lastOrderSummary.itemCount }} item(s) totaling
          {{ formatCurrency(lastOrderSummary.totalCost) }} has been submitted for processing.
        </p>
        <button class="btn-primary" @click="resetForm">Restock Again</button>
      </div>
    </div>

    <!-- Recommendations Card -->
    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">Recommendations</h3>
      </div>

      <div v-if="loading" class="loading">Loading recommendations...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        No items need restocking with the current budget and filters.
      </div>
      <div v-else>
        <div class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item</th>
                <th>Category</th>
                <th>Warehouse</th>
                <th class="col-number">On Hand</th>
                <th class="col-number">Reorder Pt</th>
                <th class="col-number">Qty to Order</th>
                <th class="col-number">Unit Cost</th>
                <th class="col-number">Est. Cost</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku + '-' + rec.warehouse">
                <td><code class="sku-code">{{ rec.sku }}</code></td>
                <td class="item-name">{{ rec.name }}</td>
                <td>{{ rec.category }}</td>
                <td>{{ rec.warehouse }}</td>
                <td class="col-number">{{ rec.current_stock }}</td>
                <td class="col-number">{{ rec.reorder_point }}</td>
                <td class="col-number"><strong>{{ rec.recommended_quantity }}</strong></td>
                <td class="col-number">{{ formatCurrency(rec.unit_cost) }}</td>
                <td class="col-number"><strong>{{ formatCurrency(rec.estimated_cost) }}</strong></td>
                <td>
                  <span :class="['badge', rec.source === 'forecast' ? 'badge-forecast' : 'badge-reorder']">
                    {{ rec.source === 'forecast' ? 'Forecast' : 'Reorder Point' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Order Summary Footer -->
        <div class="order-footer">
          <span class="order-summary">
            {{ recommendations.length }} item{{ recommendations.length !== 1 ? 's' : '' }},
            Total: <strong>{{ formatCurrency(totalEstimatedCost) }}</strong>
          </span>
          <button
            class="btn-primary"
            :disabled="!canPlaceOrder || placingOrder"
            @click="placeOrder"
          >
            {{ placingOrder ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const budget = ref(10000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)
    const orderPlaced = ref(false)
    const placingOrder = ref(false)
    const lastOrderSummary = ref({ itemCount: 0, totalCost: 0 })

    // Debounce timer handle
    let debounceTimer = null

    const formattedBudget = computed(() => formatCurrency(budget.value))

    const totalEstimatedCost = computed(() =>
      recommendations.value.reduce((sum, rec) => sum + (rec.estimated_cost || 0), 0)
    )

    const canPlaceOrder = computed(() => recommendations.value.length > 0)

    const formatCurrency = (value) => {
      const symbol = currencySymbol.value
      return `${symbol}${Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
    }

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const data = await api.getRestockingRecommendations(budget.value, filters)
        recommendations.value = data
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + (err.message || 'Unknown error')
        console.error('Restocking load error:', err)
      } finally {
        loading.value = false
      }
    }

    const onBudgetInput = (event) => {
      budget.value = Number(event.target.value)
      // Debounce the API call by 300ms
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      placingOrder.value = true
      error.value = null
      try {
        const orderData = {
          items: recommendations.value.map(rec => ({
            sku: rec.sku,
            name: rec.name,
            warehouse: rec.warehouse,
            quantity: rec.recommended_quantity,
            unit_cost: rec.unit_cost
          })),
          budget: budget.value,
          total_cost: totalEstimatedCost.value
        }
        await api.placeRestockingOrder(orderData)
        lastOrderSummary.value = {
          itemCount: recommendations.value.length,
          totalCost: totalEstimatedCost.value
        }
        orderPlaced.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + (err.message || 'Unknown error')
        console.error('Place order error:', err)
      } finally {
        placingOrder.value = false
      }
    }

    const resetForm = () => {
      orderPlaced.value = false
      budget.value = 10000
      recommendations.value = []
      error.value = null
      loadRecommendations()
    }

    // Watch filter changes and reload
    watch([selectedLocation, selectedCategory], () => {
      loadRecommendations()
    })

    onMounted(() => {
      loadRecommendations()
    })

    return {
      budget,
      recommendations,
      loading,
      error,
      orderPlaced,
      placingOrder,
      lastOrderSummary,
      formattedBudget,
      totalEstimatedCost,
      canPlaceOrder,
      formatCurrency,
      onBudgetInput,
      placeOrder,
      resetForm
    }
  }
}
</script>

<style scoped>
.restocking {
  /* inherits .main-content padding */
}

/* Budget slider */
.budget-label {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2563eb;
}

.budget-slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.budget-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: background 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #1d4ed8;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.slider-bound {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
  min-width: 50px;
}

/* Recommendations table */
.recommendations-table {
  table-layout: auto;
  width: 100%;
}

.col-number {
  text-align: right;
}

.sku-code {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.813rem;
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  color: #334155;
}

.item-name {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Source badges */
.badge-forecast {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #dbeafe;
  color: #1e40af;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge-reorder {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #fed7aa;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Order footer */
.order-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0.75rem 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.5rem;
}

.order-summary {
  font-size: 0.938rem;
  color: #475569;
}

/* Buttons */
.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Success card */
.success-card {
  border-color: #a7f3d0;
}

.success-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  text-align: center;
  gap: 1rem;
}

.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #065f46;
}

.success-message {
  color: #374151;
  font-size: 0.938rem;
  max-width: 480px;
  line-height: 1.6;
}
</style>
