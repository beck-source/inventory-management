<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Budget-driven restocking recommendations based on demand forecasts. Adjust the budget to see which items can be restocked.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Card -->
      <div class="card">
        <div class="card-header budget-card-header">
          <span class="card-title">Budget</span>
          <span class="budget-display">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="slider-container">
          <span class="slider-label">$0</span>
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="500000"
            step="1000"
            class="budget-slider"
          />
          <span class="slider-label">$500,000</span>
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">Recommended Restocking ({{ recommendations.length }} items)</span>
          <span class="budget-summary">
            <span class="budget-used">{{ formatCurrency(totalCost) }}</span>
            of
            <span class="budget-total">{{ formatCurrency(budget) }}</span>
          </span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No items can be restocked within this budget. Try increasing the budget.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>Item Name</th>
                <th>SKU</th>
                <th>Trend</th>
                <th>Qty to Order</th>
                <th>Unit Cost</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_name }}</strong></td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td>{{ item.quantity.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ item.subtotal.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer">
          <div class="footer-total">
            Total: <strong>{{ formatCurrency(totalCost) }}</strong>
          </div>
          <div class="footer-actions">
            <div v-if="submitSuccess" class="success-message">Restocking order submitted successfully.</div>
            <div v-if="submitError" class="error-inline">{{ submitError }}</div>
            <button
              class="btn-primary"
              :disabled="submitting || recommendations.length === 0"
              @click="placeOrder"
            >
              {{ submitting ? 'Submitting...' : 'Place Order' }}
            </button>
          </div>
        </div>
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
    const { currentCurrency } = useI18n()

    const budget = ref(50000)
    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitSuccess = ref(false)
    const submitError = ref(null)

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loadForecasts = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getDemandForecasts()
        forecasts.value = Array.isArray(data) ? data : (data.items || data.forecasts || [])
      } catch (err) {
        error.value = 'Failed to load demand forecasts'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const recommendations = computed(() => {
      const TREND_PRIORITY = { increasing: 0, stable: 1, decreasing: 2 }

      const eligible = forecasts.value.filter(item => {
        const gap = (item.forecasted_demand ?? 0) - (item.current_demand ?? 0)
        return gap > 0
      })

      const sorted = [...eligible].sort((a, b) => {
        const trendA = TREND_PRIORITY[a.trend] ?? 99
        const trendB = TREND_PRIORITY[b.trend] ?? 99
        if (trendA !== trendB) return trendA - trendB
        const gapA = (a.forecasted_demand ?? 0) - (a.current_demand ?? 0)
        const gapB = (b.forecasted_demand ?? 0) - (b.current_demand ?? 0)
        return gapB - gapA
      })

      let remaining = budget.value
      const selected = []

      for (const item of sorted) {
        const gap = (item.forecasted_demand ?? 0) - (item.current_demand ?? 0)
        const unitCost = item.unit_cost ?? 0
        const subtotal = Math.round(gap * unitCost * 100) / 100

        if (subtotal <= remaining) {
          selected.push({
            item_sku: item.item_sku ?? item.sku,
            item_name: item.item_name ?? item.name,
            trend: item.trend,
            quantity: gap,
            unit_cost: unitCost,
            subtotal
          })
          remaining -= subtotal
        }
      }

      return selected
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.subtotal, 0)
    })

    const placeOrder = async () => {
      submitting.value = true
      submitSuccess.value = false
      submitError.value = null
      try {
        await api.createRestockingOrder({
          items: recommendations.value,
          total_cost: totalCost.value,
          budget: budget.value
        })
        submitSuccess.value = true
      } catch (err) {
        submitError.value = 'Failed to submit restocking order. Please try again.'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
      })
    }

    onMounted(() => loadForecasts())

    return {
      budget,
      forecasts,
      loading,
      error,
      submitting,
      submitSuccess,
      submitError,
      currencySymbol,
      recommendations,
      totalCost,
      loadForecasts,
      placeOrder,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card-header {
  justify-content: space-between;
  align-items: center;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0 0.5rem;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-summary {
  font-size: 0.938rem;
  color: #64748b;
}

.budget-used {
  font-weight: 700;
  color: #0f172a;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0.75rem 0.5rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
}

.footer-total {
  font-size: 1rem;
  color: #0f172a;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-message {
  color: #059669;
  font-size: 0.875rem;
  font-weight: 500;
}

.error-inline {
  color: #dc2626;
  font-size: 0.875rem;
}
</style>
