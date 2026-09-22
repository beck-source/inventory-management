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
        </div>
        <div class="budget-content">
          <div class="slider-container">
            <div class="budget-display">
              <div class="budget-amount">
                <span class="label">Available Budget:</span>
                <span class="amount">{{ currencySymbol }}{{ selectedBudget.toLocaleString() }}</span>
              </div>
              <div class="budget-remaining">
                <span class="label">Remaining:</span>
                <span class="amount" :class="{ 'overspent': remainingBudget < 0 }">
                  {{ currencySymbol }}{{ remainingBudget.toLocaleString() }}
                </span>
              </div>
            </div>
            <input
              v-model.number="selectedBudget"
              type="range"
              min="5000"
              max="100000"
              step="5000"
              class="budget-slider"
            />
            <div class="slider-labels">
              <span>$5K</span>
              <span>{{ currencySymbol }}{{ (selectedBudget / 1000).toFixed(0) }}K</span>
              <span>$100K</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendations Section -->
      <div class="card recommendations-card">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Items for Restocking ({{ recommendedItems.length }} items)
          </h3>
          <p class="card-subtitle">Based on demand forecast, sorted by highest demand</p>
        </div>

        <div v-if="recommendedItems.length === 0" class="no-recommendations">
          <p>{{ t('restocking.noRecommendations') }}</p>
        </div>

        <div v-else class="recommendations-list">
          <div
            v-for="item in recommendedItems"
            :key="item.sku"
            class="recommendation-item"
            :class="{ selected: selectedItems.includes(item.sku), 'over-budget': getItemTotalCost(item) > remainingBudget }"
          >
            <div class="item-select">
              <input
                type="checkbox"
                :id="`item-${item.sku}`"
                :checked="selectedItems.includes(item.sku)"
                :disabled="getItemTotalCost(item) > remainingBudget && !selectedItems.includes(item.sku)"
                @change="toggleItem(item.sku)"
              />
            </div>
            <label :for="`item-${item.sku}`" class="item-info">
              <div class="item-header">
                <span class="item-sku">{{ item.sku }}</span>
                <span class="item-name">{{ item.name }}</span>
              </div>
              <div class="item-metrics">
                <span class="metric">
                  <strong>Demand:</strong> {{ item.forecasted_demand }} units
                  <span class="trend-badge" :class="`trend-${item.trend}`">{{ item.trend }}</span>
                </span>
                <span class="metric">
                  <strong>Unit Cost:</strong> {{ currencySymbol }}{{ item.unit_cost }}
                </span>
                <span class="metric">
                  <strong>Qty:</strong>
                  <input
                    type="number"
                    :value="getItemQuantity(item.sku)"
                    :min="1"
                    :max="item.forecasted_demand * 2"
                    @change="updateItemQuantity(item.sku, $event.target.value)"
                    @click.stop
                    class="qty-input"
                  />
                </span>
                <span class="metric cost">
                  <strong>Total:</strong> {{ currencySymbol }}{{ getItemTotalCost(item).toLocaleString() }}
                </span>
              </div>
            </label>
          </div>
        </div>

        <!-- Order Summary -->
        <div class="order-summary">
          <div class="summary-row">
            <span>Items Selected:</span>
            <strong>{{ selectedItems.length }}</strong>
          </div>
          <div class="summary-row">
            <span>Total Units:</span>
            <strong>{{ totalUnits }}</strong>
          </div>
          <div class="summary-row total-cost">
            <span>Total Cost:</span>
            <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong>
          </div>
          <div class="summary-row" :class="{ warning: remainingBudget < 0 }">
            <span>Budget Remaining:</span>
            <strong :class="{ overspent: remainingBudget < 0 }">
              {{ currencySymbol }}{{ remainingBudget.toLocaleString() }}
            </strong>
          </div>
        </div>

        <div class="action-buttons">
          <button
            class="btn btn-primary"
            :disabled="selectedItems.length === 0 || remainingBudget < 0 || submitting"
            @click="submitOrder"
          >
            <span v-if="!submitting">{{ t('restocking.placeOrder') }}</span>
            <span v-else>Submitting...</span>
          </button>
          <button class="btn btn-secondary" @click="clearSelection">Clear Selection</button>
        </div>
      </div>

      <!-- Restocking History (Last 5 orders from localStorage) -->
      <div v-if="recentOrders.length > 0" class="card history-card">
        <div class="card-header">
          <h3 class="card-title">Recent Restocking Orders</h3>
        </div>
        <div class="table-container">
          <table class="history-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Date</th>
                <th>Items</th>
                <th>Total Units</th>
                <th>Total Cost</th>
                <th>Lead Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in recentOrders" :key="order.id">
                <td><strong>{{ order.id.substring(0, 8) }}...</strong></td>
                <td>{{ formatDate(order.date) }}</td>
                <td>{{ order.items.length }}</td>
                <td>{{ order.total_units }}</td>
                <td><strong>{{ currencySymbol }}{{ order.total_cost.toLocaleString() }}</strong></td>
                <td>
                  <span class="lead-time">{{ order.lead_time }} days</span>
                </td>
                <td>
                  <span class="badge badge-submitted">{{ t('status.submitted') }}</span>
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
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const selectedBudget = ref(50000) // Default $50K
    const demands = ref([])
    const inventoryMap = ref({}) // SKU -> inventory item
    const selectedItems = ref([]) // Selected SKUs
    const itemQuantities = ref({}) // SKU -> quantity to order

    // Load data on mount
    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        // Get demand forecasts
        demands.value = await api.getDemandForecasts()

        // Get inventory to build SKU -> item map with pricing
        const inventory = await api.getInventory()
        inventoryMap.value = {}
        inventory.forEach(item => {
          inventoryMap.value[item.sku] = item
        })
      } catch (err) {
        error.value = 'Failed to load forecast and inventory data'
        console.error('Load error:', err)
      } finally {
        loading.value = false
      }
    }

    // Build recommended items list
    const recommendedItems = computed(() => {
      return demands.value
        .map(demand => {
          const inventoryItem = inventoryMap.value[demand.item_sku]
          if (!inventoryItem) return null

          return {
            sku: demand.item_sku,
            name: demand.item_name,
            unit_cost: inventoryItem.unit_cost,
            forecasted_demand: demand.forecasted_demand,
            trend: demand.trend
          }
        })
        .filter(Boolean)
        .sort((a, b) => b.forecasted_demand - a.forecasted_demand) // Sort by highest demand
    })

    // Computed properties for budget tracking
    const totalCost = computed(() => {
      return selectedItems.value.reduce((sum, sku) => {
        const item = recommendedItems.value.find(i => i.sku === sku)
        if (!item) return sum
        const qty = itemQuantities.value[sku] || item.forecasted_demand
        return sum + item.unit_cost * qty
      }, 0)
    })

    const remainingBudget = computed(() => {
      return selectedBudget.value - totalCost.value
    })

    const totalUnits = computed(() => {
      return selectedItems.value.reduce((sum, sku) => {
        const item = recommendedItems.value.find(i => i.sku === sku)
        if (!item) return sum
        const qty = itemQuantities.value[sku] || item.forecasted_demand
        return sum + parseInt(qty, 10)
      }, 0)
    })

    // Get recent restocking orders from localStorage
    const recentOrders = computed(() => {
      const stored = localStorage.getItem('restocking_orders')
      const orders = stored ? JSON.parse(stored) : []
      return orders.slice(0, 5) // Last 5 orders
    })

    // Helper methods
    const toggleItem = (sku) => {
      const index = selectedItems.value.indexOf(sku)
      if (index > -1) {
        selectedItems.value.splice(index, 1)
        delete itemQuantities.value[sku]
      } else {
        selectedItems.value.push(sku)
        const item = recommendedItems.value.find(i => i.sku === sku)
        if (item) {
          itemQuantities.value[sku] = item.forecasted_demand
        }
      }
    }

    const getItemQuantity = (sku) => {
      const item = recommendedItems.value.find(i => i.sku === sku)
      return itemQuantities.value[sku] || (item ? item.forecasted_demand : 0)
    }

    const updateItemQuantity = (sku, value) => {
      const qty = parseInt(value, 10)
      if (qty > 0) {
        itemQuantities.value[sku] = qty
      }
    }

    const getItemTotalCost = (item) => {
      const qty = itemQuantities.value[item.sku] || item.forecasted_demand
      return item.unit_cost * qty
    }

    const clearSelection = () => {
      selectedItems.value = []
      itemQuantities.value = {}
    }

    const submitOrder = async () => {
      if (selectedItems.value.length === 0 || remainingBudget.value < 0) return

      try {
        submitting.value = true

        // Build order object
        const orderItems = selectedItems.value.map(sku => {
          const item = recommendedItems.value.find(i => i.sku === sku)
          const qty = itemQuantities.value[sku] || item.forecasted_demand
          return {
            sku: sku,
            name: item.name,
            quantity: qty,
            unit_cost: item.unit_cost,
            total: item.unit_cost * qty
          }
        })

        const restockingOrder = {
          id: `RSO-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          date: new Date().toISOString(),
          items: orderItems,
          total_units: totalUnits.value,
          total_cost: totalCost.value,
          lead_time: generateRandomLeadTime() // Random 2-5 days
        }

        // Save to localStorage
        const stored = localStorage.getItem('restocking_orders')
        const orders = stored ? JSON.parse(stored) : []
        orders.unshift(restockingOrder) // Add to beginning
        localStorage.setItem('restocking_orders', JSON.stringify(orders))

        // Also save to a persisted order in app state so Orders.vue can access it
        const allOrders = localStorage.getItem('submitted_orders')
        const submittedOrders = allOrders ? JSON.parse(allOrders) : []
        submittedOrders.unshift({
          id: restockingOrder.id,
          order_number: `REST-${restockingOrder.id.substring(4, 8)}`,
          customer: 'Internal Restocking',
          items: orderItems,
          status: 'Submitted',
          order_date: new Date().toISOString().split('T')[0],
          expected_delivery: getExpectedDelivery(restockingOrder.lead_time),
          total_value: restockingOrder.total_cost,
          lead_time: restockingOrder.lead_time,
          is_restocking: true
        })
        localStorage.setItem('submitted_orders', JSON.stringify(submittedOrders))

        // Show success message (you could use a toast here)
        alert(`Restocking order placed successfully!\nOrder ID: ${restockingOrder.id}\nLead Time: ${restockingOrder.lead_time} days`)

        // Clear selection and reset
        clearSelection()
      } catch (err) {
        console.error('Error submitting order:', err)
        alert('Failed to submit restocking order')
      } finally {
        submitting.value = false
      }
    }

    const generateRandomLeadTime = () => {
      return Math.floor(Math.random() * 4) + 2 // Random between 2-5 days
    }

    const getExpectedDelivery = (leadTimeDays) => {
      const date = new Date()
      date.setDate(date.getDate() + leadTimeDays)
      return date.toISOString().split('T')[0]
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    onMounted(loadData)

    return {
      t,
      currencySymbol,
      loading,
      error,
      submitting,
      selectedBudget,
      recommendedItems,
      selectedItems,
      totalCost,
      remainingBudget,
      totalUnits,
      recentOrders,
      toggleItem,
      getItemQuantity,
      updateItemQuantity,
      getItemTotalCost,
      clearSelection,
      submitOrder,
      formatDate
    }
  }
}
</script>

<style scoped>
.restocking {
  width: 100%;
}

.budget-card {
  margin-bottom: 1.5rem;
}

.budget-content {
  padding: 1.5rem;
}

.budget-display {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--color-surface-alt);
  border-radius: 8px;
}

.budget-amount,
.budget-remaining {
  display: flex;
  flex-direction: column;
}

.budget-amount .label,
.budget-remaining .label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.budget-amount .amount,
.budget-remaining .amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.budget-remaining .amount.overspent {
  color: var(--color-danger);
}

.slider-container {
  padding: 1rem 0;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 5px;
  background: var(--color-border);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  margin: 1rem 0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  box-shadow: var(--shadow-md);
}

.budget-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  box-shadow: var(--shadow-md);
  border: none;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-top: 0.5rem;
}

.recommendations-card {
  margin-bottom: 1.5rem;
}

.card-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
  font-weight: 400;
}

.no-recommendations {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  transition: all 0.2s ease;
}

.recommendation-item:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-alt);
}

.recommendation-item.selected {
  border-color: var(--color-accent);
  background: var(--color-accent-subtle);
}

.recommendation-item.over-budget {
  opacity: 0.6;
}

.recommendation-item input[type='checkbox']:disabled {
  cursor: not-allowed;
}

.item-select {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding-top: 0.25rem;
}

.item-select input[type='checkbox'] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-accent);
}

label {
  flex: 1;
  cursor: pointer;
  user-select: none;
}

.item-header {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.item-sku {
  font-weight: 700;
  color: var(--color-accent);
  font-size: 0.875rem;
}

.item-name {
  font-weight: 500;
  color: var(--color-text-primary);
  flex: 1;
}

.item-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.813rem;
  color: var(--color-text-secondary);
}

.metric {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.metric.cost {
  font-weight: 600;
  color: var(--color-text-primary);
  margin-left: auto;
}

.trend-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-left: 0.5rem;
}

.trend-badge.trend-increasing {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.trend-badge.trend-stable {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.trend-badge.trend-decreasing {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.qty-input {
  width: 60px;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.813rem;
  text-align: center;
}

.qty-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--shadow-focus);
}

.order-summary {
  padding: 1.5rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-alt);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.938rem;
  color: var(--color-text-secondary);
}

.summary-row strong {
  color: var(--color-text-primary);
}

.summary-row.total-cost {
  padding: 1rem 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.summary-row.total-cost strong {
  color: var(--color-accent);
  font-size: 1.25rem;
}

.summary-row.warning {
  color: var(--color-warning-text);
}

.summary-row.warning strong {
  color: var(--color-warning);
}

.summary-row.warning.overspent strong {
  color: var(--color-danger);
}

.action-buttons {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--color-accent);
  color: var(--color-on-accent);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.btn-secondary:hover {
  background: var(--color-border);
}

.history-card {
  margin-bottom: 1.5rem;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table thead {
  background: var(--color-surface-alt);
}

.history-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
}

.history-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.lead-time {
  font-weight: 600;
  color: var(--color-text-primary);
}

.badge-submitted {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}
</style>
