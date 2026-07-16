<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Get automatic restocking recommendations based on a budget</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Budget</h3>
      </div>
      <div class="budget-control">
        <input
          type="range"
          min="0"
          max="50000"
          step="500"
          v-model.number="budget"
          class="budget-slider"
        />
        <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="summary-line">
        <div class="summary-item">
          <span class="summary-label">Budget</span>
          <span class="summary-value">{{ currencySymbol }}{{ recommendations.budget.toLocaleString() }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Allocated</span>
          <span class="summary-value">{{ currencySymbol }}{{ recommendations.allocated_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Remaining</span>
          <span class="summary-value">{{ currencySymbol }}{{ recommendations.remaining_budget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommendations ({{ recommendations.items.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="loading || recommendations.items.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="orderSuccess" class="order-success">
          Order {{ orderSuccess.order_number }} placed successfully — expected lead time {{ orderSuccess.lead_time_days }} days.
        </div>
        <div v-if="orderError" class="order-error">{{ orderError }}</div>

        <div v-if="recommendations.items.length === 0" class="empty-state">
          No items to recommend for the current budget and filters.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Category</th>
                <th>Warehouse</th>
                <th>Qty On Hand</th>
                <th>Reorder Point</th>
                <th>Recommended Qty</th>
                <th>Unit Cost</th>
                <th>Line Cost</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.warehouse }}</td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.reorder_point }}</td>
                <td>
                  {{ item.recommended_quantity }}
                  <span v-if="!item.fully_funded" class="partial-note">
                    (partial — needs {{ item.target_quantity }})
                  </span>
                </td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ item.trend }}
                  </span>
                </td>
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
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(5000)
    const recommendations = ref({ budget: 0, allocated_cost: 0, remaining_budget: 0, items: [] })

    const submitting = ref(false)
    const orderSuccess = ref(null)
    const orderError = ref(null)

    // Only warehouse/category filters apply to restocking (no time dimension)
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        recommendations.value = await api.getRestockingRecommendations(budget.value, filters)
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    watch([selectedLocation, selectedCategory], () => {
      loadRecommendations()
    })

    const placeOrder = async () => {
      submitting.value = true
      orderSuccess.value = null
      orderError.value = null
      try {
        const filters = getCurrentFilters()
        const order = await api.createRestockingOrder(budget.value, filters)
        orderSuccess.value = order
        // Refresh recommendations to reflect the newly placed order's impact
        await loadRecommendations()
      } catch (err) {
        orderError.value = err.response?.data?.detail || 'Failed to place restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      loading,
      error,
      budget,
      recommendations,
      submitting,
      orderSuccess,
      orderError,
      currencySymbol,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
}

.budget-readout {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.summary-line {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
  padding: 1rem 1.25rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
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

.place-order-btn {
  background: #2563eb;
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
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.order-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.partial-note {
  display: block;
  font-size: 0.75rem;
  color: #92400e;
  font-style: italic;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
