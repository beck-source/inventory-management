<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Allocate budget to restock items based on demand forecasts</p>
    </div>

    <div v-if="successBanner.visible" class="success-banner">
      <span>
        Order <strong>{{ successBanner.orderNumber }}</strong> submitted successfully.
        Navigate to the Orders tab to track delivery.
      </span>
      <button class="banner-close" @click="dismissBanner">&#x2715;</button>
    </div>

    <div v-if="loading" class="loading">Loading demand forecasts...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-section">
          <div class="slider-wrapper">
            <input
              type="range"
              min="0"
              max="50000"
              step="500"
              v-model.number="budget"
              class="budget-slider"
            />
            <div class="slider-labels">
              <span>$0</span>
              <span>$50,000</span>
            </div>
          </div>
          <div class="budget-display">
            <div class="budget-amount">${{ budget.toLocaleString() }}</div>
            <div class="budget-remaining" v-if="budget > 0">
              Budget remaining: <strong>${{ budgetRemaining.toLocaleString() }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Restocking
            <span v-if="recommendations.length > 0" class="badge info title-badge">
              {{ recommendations.length }} item{{ recommendations.length !== 1 ? 's' : '' }}
            </span>
          </h3>
        </div>

        <div v-if="budget === 0" class="empty-note">
          Set a budget above to see recommendations
        </div>
        <div v-else-if="recommendations.length === 0" class="empty-note">
          No items fit within the current budget
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>Item Name</th>
                <th>SKU</th>
                <th>Demand Gap</th>
                <th>Qty to Order</th>
                <th>Unit Cost</th>
                <th>Line Total</th>
                <th>Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td>
                  <span class="item-name-cell">
                    {{ item.item_name }}
                    <span :class="['badge', item.trend]">{{ item.trend }}</span>
                  </span>
                </td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.demand_gap }}</td>
                <td><strong>{{ item.qty_to_order }}</strong></td>
                <td>${{ item.unit_cost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
                <td><strong>${{ item.line_total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
                <td>
                  <span class="lead-time-cell">{{ item.lead_days }} days</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="place-order-row">
        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || placingOrder"
          @click="placeOrder"
        >
          <span v-if="placingOrder">Submitting order...</span>
          <span v-else>
            Place Restocking Order &mdash; ${{ totalCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
          </span>
        </button>
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
    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)
    const budget = ref(25000)
    const placingOrder = ref(false)
    const successBanner = ref({ visible: false, orderNumber: '' })
    let dismissTimer = null

    const recommendations = computed(() => {
      if (budget.value === 0) return []

      const candidates = forecasts.value
        .filter(f => (f.forecasted_demand - f.current_demand) > 0)
        .map(f => ({
          ...f,
          demand_gap: f.forecasted_demand - f.current_demand
        }))
        .sort((a, b) => b.demand_gap - a.demand_gap)

      let remaining = budget.value
      const result = []

      for (const forecast of candidates) {
        const unitCost = forecast.unit_cost || 0
        if (unitCost <= 0) continue

        const affordable = Math.floor(remaining / unitCost)
        const qty = Math.min(forecast.demand_gap, affordable)

        if (qty > 0) {
          const leadDays = forecast.trend === 'increasing' ? 21 : forecast.trend === 'stable' ? 14 : 7
          const lineTotal = qty * unitCost
          result.push({
            ...forecast,
            qty_to_order: qty,
            line_total: lineTotal,
            lead_days: leadDays
          })
          remaining -= lineTotal
        }
      }

      return result
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.line_total, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - totalCost.value
    })

    const loadForecasts = async () => {
      loading.value = true
      error.value = null
      try {
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || placingOrder.value) return

      placingOrder.value = true
      try {
        const order = await api.createRestockingOrder({
          items: recommendations.value.map(r => ({
            sku: r.item_sku,
            name: r.item_name,
            quantity: r.qty_to_order,
            unit_price: r.unit_cost,
            lead_days: r.lead_days
          })),
          total_value: totalCost.value
        })

        successBanner.value = {
          visible: true,
          orderNumber: order.order_number
        }

        if (dismissTimer) clearTimeout(dismissTimer)
        dismissTimer = setTimeout(() => {
          successBanner.value.visible = false
        }, 6000)
      } catch (err) {
        error.value = 'Failed to place restocking order'
        console.error(err)
      } finally {
        placingOrder.value = false
      }
    }

    const dismissBanner = () => {
      successBanner.value.visible = false
      if (dismissTimer) clearTimeout(dismissTimer)
    }

    onMounted(loadForecasts)

    return {
      forecasts,
      loading,
      error,
      budget,
      placingOrder,
      successBanner,
      recommendations,
      totalCost,
      budgetRemaining,
      placeOrder,
      dismissBanner
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.banner-close {
  background: none;
  border: none;
  color: #065f46;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  line-height: 1;
  flex-shrink: 0;
  margin-left: 1rem;
  transition: background 0.15s ease;
}

.banner-close:hover {
  background: #a7f3d0;
}

.budget-section {
  display: flex;
  gap: 2.5rem;
  align-items: center;
}

.slider-wrapper {
  flex: 1;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  accent-color: #2563eb;
  display: block;
  margin-bottom: 0.5rem;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
  transition: box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 1px 8px rgba(37, 99, 235, 0.5);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
}

.budget-display {
  flex-shrink: 0;
  text-align: right;
  min-width: 200px;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.1;
  margin-bottom: 0.375rem;
}

.budget-remaining {
  font-size: 0.875rem;
  color: #64748b;
}

.title-badge {
  margin-left: 0.75rem;
  vertical-align: middle;
  font-size: 0.75rem;
}

.empty-note {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

.item-name-cell {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.lead-time-cell {
  font-size: 0.875rem;
  color: #475569;
  white-space: nowrap;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.25rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease;
  letter-spacing: -0.01em;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
