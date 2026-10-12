<template>
  <div class="restocking">
    <EuAiActBanner page="restocking" />

    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Prioritize restock orders based on demand forecasts and an adjustable budget.</p>
    </div>

    <div v-if="loading" class="loading">Loading restocking data...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Stat Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Candidates</div>
          <div class="stat-value">{{ candidates.length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">Budget Required</div>
          <div class="stat-value">${{ totalCandidateCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Items Recommended</div>
          <div class="stat-value">{{ recommended.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Budget Used</div>
          <div class="stat-value">${{ budgetUsed.toLocaleString() }}</div>
        </div>
      </div>

      <!-- Budget Slider Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget Allocation</h3>
          <span class="budget-label">${{ budget.toLocaleString() }} of ${{ sliderMax.toLocaleString() }}</span>
        </div>
        <div class="slider-section">
          <input
            type="range"
            :min="0"
            :max="sliderMax"
            :step="100"
            v-model.number="budget"
          />
          <div class="budget-usage-text">
            ${{ budgetUsed.toLocaleString() }} of ${{ budget.toLocaleString() }} used
          </div>
          <div class="budget-bar-track">
            <div
              class="budget-bar-fill"
              :style="{ width: budgetUtilizationPct + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Success Banner -->
      <transition name="fade">
        <div v-if="showSuccess" class="success-banner">
          Order submitted successfully. Your restocking order has been queued for fulfillment.
        </div>
      </transition>

      <!-- Recommended Items Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommended.length }})</h3>
          <button
            class="btn-primary"
            :disabled="recommended.length === 0"
            @click="handlePlaceOrder"
          >
            Place Order
          </button>
        </div>

        <div v-if="recommended.length === 0" class="empty-state">
          Adjust the budget slider to include items in your order.
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>Item Name</th>
                <th>SKU</th>
                <th>Category</th>
                <th>Trend</th>
                <th>Forecast Gap</th>
                <th>Lead Time</th>
                <th>Est. Delivery</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommended" :key="item.item_sku">
                <td><strong>{{ item.item_name }}</strong></td>
                <td class="sku-cell">{{ item.item_sku }}</td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td class="numeric-cell">{{ item.restock_qty }} units</td>
                <td class="numeric-cell">{{ item.lead_time_days }}d</td>
                <td>{{ item.est_delivery }}</td>
                <td class="numeric-cell">${{ item.unit_cost.toLocaleString() }}</td>
                <td class="numeric-cell">
                  <strong>${{ (item.restock_qty * item.unit_cost).toLocaleString() }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- All Candidates Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">All Restock Candidates ({{ candidates.length }})</h3>
        </div>
        <div v-if="candidates.length === 0" class="empty-state">
          No restock candidates found. All items are within forecast demand.
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>Item Name</th>
                <th>SKU</th>
                <th>Category</th>
                <th>Trend</th>
                <th>Current Demand</th>
                <th>Forecasted Demand</th>
                <th>Forecast Gap</th>
                <th>Lead Time</th>
                <th>Est. Delivery</th>
                <th>Unit Cost</th>
                <th>Full Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in candidates" :key="item.item_sku">
                <td><strong>{{ item.item_name }}</strong></td>
                <td class="sku-cell">{{ item.item_sku }}</td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td class="numeric-cell">{{ item.current_demand }}</td>
                <td class="numeric-cell">{{ item.forecasted_demand }}</td>
                <td class="numeric-cell">{{ item.restock_qty }} units</td>
                <td class="numeric-cell">{{ item.lead_time_days }}d</td>
                <td>{{ item.est_delivery }}</td>
                <td class="numeric-cell">${{ item.unit_cost.toLocaleString() }}</td>
                <td class="numeric-cell">
                  <strong>${{ item.full_cost.toLocaleString() }}</strong>
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
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useRestockingOrders } from '../composables/useRestockingOrders'
import { useWorksCouncil } from '../composables/useWorksCouncil'
import EuAiActBanner from '../components/EuAiActBanner.vue'

const LEAD_TIME_DAYS = { increasing: 3, stable: 7, decreasing: 14 }

function formatDeliveryDate(leadTimeDays) {
  const today = new Date()
  today.setDate(today.getDate() + leadTimeDays)
  return today.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default {
  name: 'Restocking',
  components: { EuAiActBanner },
  setup() {
    const { submitOrder } = useRestockingOrders()
    const { requireApproval } = useWorksCouncil()

    const loading = ref(true)
    const error = ref(null)
    const showSuccess = ref(false)

    // Raw data
    const demandForecasts = ref([])
    const inventoryItems = ref([])

    // Budget slider state
    const budget = ref(0)

    // Join demand forecasts with inventory to build enriched candidate list
    const enrichedDemand = computed(() => {
      return demandForecasts.value.map(demand => {
        const invItem = inventoryItems.value.find(inv => inv.sku === demand.item_sku)
        if (!invItem) return null

        const leadTimeDays = LEAD_TIME_DAYS[demand.trend] ?? 7

        return {
          id: demand.id,
          item_sku: demand.item_sku,
          item_name: demand.item_name,
          category: invItem.category,
          current_demand: demand.current_demand,
          forecasted_demand: demand.forecasted_demand,
          trend: demand.trend,
          unit_cost: invItem.unit_cost ?? 0,
          lead_time_days: leadTimeDays,
          est_delivery: formatDeliveryDate(leadTimeDays)
        }
      }).filter(item => item !== null)
    })

    // Restock candidates: items where forecasted > current, sorted by gap descending
    const candidates = computed(() => {
      return enrichedDemand.value
        .filter(item => item.forecasted_demand > item.current_demand)
        .map(item => {
          const restock_qty = item.forecasted_demand - item.current_demand
          return {
            ...item,
            restock_qty,
            full_cost: restock_qty * item.unit_cost
          }
        })
        .sort((a, b) => b.restock_qty - a.restock_qty)
    })

    // Total cost if all candidates fully restocked
    const totalCandidateCost = computed(() => {
      return candidates.value.reduce((sum, item) => sum + item.full_cost, 0)
    })

    // Slider max — round up to nearest 1000
    const sliderMax = computed(() => {
      return Math.ceil(totalCandidateCost.value / 1000) * 1000
    })

    // Greedy fill: walk sorted candidates, add as many full units as budget allows
    const recommended = computed(() => {
      let remaining = budget.value
      const result = []

      for (const item of candidates.value) {
        if (remaining <= 0) break

        const fullCost = item.restock_qty * item.unit_cost

        if (fullCost <= remaining) {
          result.push({ ...item })
          remaining -= fullCost
        } else if (remaining > 0 && item.unit_cost > 0) {
          const partialQty = Math.floor(remaining / item.unit_cost)
          if (partialQty > 0) {
            result.push({
              ...item,
              restock_qty: partialQty,
              full_cost: partialQty * item.unit_cost
            })
            remaining -= partialQty * item.unit_cost
          }
        }
      }

      return result
    })

    // Budget actually consumed by recommended items
    const budgetUsed = computed(() => {
      return recommended.value.reduce((sum, item) => sum + item.restock_qty * item.unit_cost, 0)
    })

    // Utilization percentage for progress bar
    const budgetUtilizationPct = computed(() => {
      if (budget.value === 0) return 0
      return Math.min(100, (budgetUsed.value / budget.value) * 100)
    })

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
        // Default slider to full max after data loads — use nextTick-equivalent via watch
        // We set it after candidates/sliderMax are computed by setting in next microtask
        Promise.resolve().then(() => {
          budget.value = sliderMax.value
        })
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrderInternal = () => {
      submitOrder(recommended.value, budgetUsed.value)
      showSuccess.value = true
      budget.value = 0
      setTimeout(() => {
        showSuccess.value = false
      }, 3000)
    }

    const handlePlaceOrder = () => {
      if (recommended.value.length === 0) return
      if (budgetUsed.value > 5000) {
        const description = `Place restocking order for $${budgetUsed.value.toLocaleString()} (${recommended.value.length} items)`
        requireApproval(description, placeOrderInternal)
      } else {
        placeOrderInternal()
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      showSuccess,
      budget,
      candidates,
      recommended,
      totalCandidateCost,
      sliderMax,
      budgetUsed,
      budgetUtilizationPct,
      handlePlaceOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  /* inherits .main-content padding from App.vue */
}

.budget-label {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.slider-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

input[type="range"] {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
  height: 6px;
}

.budget-usage-text {
  font-size: 0.875rem;
  color: #4b5563;
  font-weight: 500;
}

.budget-bar-track {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.budget-bar-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 4px;
  transition: width 0.2s ease;
}

.restock-table {
  width: 100%;
  border-collapse: collapse;
}

.sku-cell {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.813rem;
  color: #475569;
}

.numeric-cell {
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #4b5563;
  font-size: 0.938rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
