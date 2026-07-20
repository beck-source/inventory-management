<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and review demand-driven restock recommendations</p>
    </div>

    <div v-if="loading" class="loading">Loading restock candidates...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="confirmation" class="confirmation-banner">
        <strong>Order {{ confirmation.order_number }} submitted.</strong>
        Expected delivery {{ formatDate(confirmation.expected_delivery) }} &middot;
        Total {{ formatCurrency(confirmation.total_value) }}
        <button class="dismiss-btn" @click="confirmation = null">Dismiss</button>
      </div>

      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            class="budget-slider"
            :min="0"
            :max="maxBudget"
            :step="sliderStep"
            v-model.number="budget"
          />
          <input
            type="number"
            class="budget-input"
            :min="0"
            :max="maxBudget"
            :step="sliderStep"
            v-model.number="budget"
          />
        </div>
        <div class="budget-meta">
          <span>$0</span>
          <span>Max: {{ formatCurrency(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Recommended Items</div>
          <div class="stat-value">{{ summary.itemCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Recommended Cost</div>
          <div class="stat-value">{{ formatCurrency(summary.totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Budget Remaining</div>
          <div class="stat-value">{{ formatCurrency(summary.remaining) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Restock Items ({{ recommendations.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          Increase the budget to generate restock recommendations.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item</th>
                <th>Category</th>
                <th>Demand</th>
                <th>Recommended Qty</th>
                <th>Unit Cost</th>
                <th>Line Total</th>
                <th>Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td>{{ item.item_sku }}</td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.current_demand }} &rarr; {{ item.forecasted_demand }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ formatCurrency(item.line_total) }}</strong></td>
                <td>{{ item.lead_time_days }} days</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const candidates = ref([])

    const budget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.line_total, 0)
      if (total <= 0) return 0
      // Round up to a clean number
      const magnitude = Math.pow(10, Math.max(0, Math.floor(Math.log10(total)) - 1))
      return Math.ceil(total / magnitude) * magnitude
    })

    const sliderStep = computed(() => {
      return Math.max(1, Math.round(maxBudget.value / 100))
    })

    const recommendations = computed(() => {
      const result = []
      let runningTotal = 0
      for (const candidate of candidates.value) {
        if (runningTotal + candidate.line_total <= budget.value) {
          result.push(candidate)
          runningTotal += candidate.line_total
        }
      }
      return result
    })

    const summary = computed(() => {
      const totalCost = recommendations.value.reduce((sum, item) => sum + item.line_total, 0)
      return {
        itemCount: recommendations.value.length,
        totalCost,
        remaining: budget.value - totalCost
      }
    })

    const formatCurrency = (value) => {
      return (value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const loadCandidates = async () => {
      try {
        loading.value = true
        error.value = null
        candidates.value = await api.getRestockCandidates()
        budget.value = maxBudget.value
      } catch (err) {
        error.value = 'Failed to load restock candidates: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      submitting.value = true
      submitError.value = null
      try {
        const payload = {
          budget: budget.value,
          items: recommendations.value.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            category: item.category,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost,
            line_total: item.line_total,
            lead_time_days: item.lead_time_days
          }))
        }
        confirmation.value = await api.submitRestockOrder(payload)
      } catch (err) {
        submitError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadCandidates)

    return {
      loading,
      error,
      candidates,
      budget,
      maxBudget,
      sliderStep,
      recommendations,
      summary,
      submitting,
      submitError,
      confirmation,
      formatCurrency,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-input {
  width: 140px;
  padding: 0.5rem 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.938rem;
  color: #0f172a;
}

.budget-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.confirmation-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.dismiss-btn {
  margin-left: auto;
  background: transparent;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  cursor: pointer;
}

.dismiss-btn:hover {
  background: #d1fae5;
}
</style>
