<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Budget-driven restocking recommendations based on demand forecasts</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Restocking Budget</h3>
          <div class="budget-amount">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <input
          v-model.number="budget"
          type="range"
          min="10000"
          max="100000"
          step="1000"
          class="budget-slider"
        />
        <div class="budget-range-labels">
          <span>{{ currencySymbol }}10,000</span>
          <span>{{ currencySymbol }}100,000</span>
        </div>

        <div class="budget-summary">
          <div class="summary-item">
            <span class="summary-label">Allocated</span>
            <span class="summary-value">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Remaining</span>
            <span class="summary-value" :class="{ danger: overBudget }">
              {{ currencySymbol }}{{ remainingBudget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
            </span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Items Selected</span>
            <span class="summary-value">{{ selectedItems.length }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Est. Lead Time</span>
            <span class="summary-value">{{ estimatedLeadTime }} day(s)</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
          <span class="card-subtitle">Sorted by highest demand forecast</span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No restocking recommendations for the current budget. Try increasing the budget.
        </div>

        <div v-else class="table-container">
          <table class="recommend-table">
            <thead>
              <tr>
                <th class="col-select"></th>
                <th>Item</th>
                <th>SKU</th>
                <th>Current Stock</th>
                <th>Demand Forecast</th>
                <th>Unit Cost</th>
                <th>Quantity to Order</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku" :class="{ 'row-disabled': !item.selected }">
                <td class="col-select">
                  <input type="checkbox" v-model="item.selected" />
                </td>
                <td><strong>{{ item.name }}</strong></td>
                <td>{{ item.sku }}</td>
                <td>{{ item.currentStock }}</td>
                <td><strong>{{ item.demandForecast }}</strong></td>
                <td>{{ currencySymbol }}{{ item.unitCost.toFixed(2) }}</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    class="qty-input"
                    :disabled="!item.selected"
                    :value="item.quantity"
                    @input="updateQuantity(item, $event.target.value)"
                  />
                </td>
                <td>
                  <strong>{{ currencySymbol }}{{ (item.quantity * item.unitCost).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="order-actions">
          <div v-if="orderError" class="error order-error">{{ orderError }}</div>
          <button
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            Place Order ({{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }})
          </button>
        </div>
      </div>

      <div v-if="lastOrder" class="card order-confirmation">
        <div class="card-header">
          <h3 class="card-title">Order Placed</h3>
          <span :class="['badge', lastOrder.synced ? 'success' : 'warning']">
            {{ lastOrder.synced ? '✓ Synced' : 'Unsaved' }}
          </span>
        </div>
        <p class="confirmation-message">{{ successMessage }}</p>
        <div class="confirmation-details">
          <div class="detail-item">
            <span class="detail-label">Order ID</span>
            <span class="detail-value">{{ lastOrder.id }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Items</span>
            <span class="detail-value">{{ lastOrder.itemCount }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Total Cost</span>
            <span class="detail-value">{{ currencySymbol }}{{ lastOrder.totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Lead Time</span>
            <span class="detail-value">{{ lastOrder.leadTimeDays }} day(s)</span>
          </div>
        </div>
        <button v-if="!lastOrder.synced" class="sync-btn" @click="syncOrder">
          Sync Order Now
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useRestocking } from '../composables/useRestocking'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { recommendItems, addRestockingOrder, calculateLeadTime, markOrderAsSaved } = useRestocking()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)

    const budget = ref(50000)
    const demandForecasts = ref([])
    const inventoryItems = ref([])
    const recommendations = ref([])

    const orderError = ref(null)
    const successMessage = ref(null)
    const lastOrder = ref(null)

    const buildRecommendations = () => {
      const items = recommendItems(budget.value, demandForecasts.value, inventoryItems.value)
      recommendations.value = items.map(item => ({ ...item, selected: true }))
    }

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])

        demandForecasts.value = forecasts
        inventoryItems.value = inventory
        buildRecommendations()
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Rebuild recommendations whenever the budget changes
    watch(budget, () => {
      buildRecommendations()
      orderError.value = null
    })

    const selectedItems = computed(() => {
      return recommendations.value.filter(item => item.selected && item.quantity > 0)
    })

    const totalCost = computed(() => {
      return selectedItems.value.reduce((sum, item) => sum + item.quantity * item.unitCost, 0)
    })

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const overBudget = computed(() => totalCost.value > budget.value)

    const estimatedLeadTime = computed(() => {
      const itemCount = selectedItems.value.reduce((sum, item) => sum + item.quantity, 0)
      return calculateLeadTime(itemCount)
    })

    const canPlaceOrder = computed(() => {
      return selectedItems.value.length > 0 && !overBudget.value
    })

    const updateQuantity = (item, value) => {
      const qty = Math.max(0, Math.floor(Number(value) || 0))
      item.quantity = qty
      orderError.value = null
    }

    const placeOrder = () => {
      orderError.value = null
      successMessage.value = null

      if (selectedItems.value.length === 0) {
        orderError.value = 'Select at least one item with a quantity greater than zero.'
        return
      }

      if (overBudget.value) {
        orderError.value = `Order total (${currencySymbol.value}${totalCost.value.toLocaleString()}) exceeds budget (${currencySymbol.value}${budget.value.toLocaleString()}).`
        return
      }

      const items = selectedItems.value.map(item => ({
        sku: item.sku,
        name: item.name,
        quantity: item.quantity,
        unitCost: item.unitCost,
        cost: item.quantity * item.unitCost
      }))

      const order = addRestockingOrder({
        items,
        totalCost: totalCost.value,
        budget: budget.value
      })

      lastOrder.value = order
      successMessage.value = `Order ${order.id} placed successfully. Estimated delivery in ${order.leadTimeDays} day(s).`
    }

    const syncOrder = () => {
      if (!lastOrder.value) return
      const updated = markOrderAsSaved(lastOrder.value.id)
      if (updated) {
        lastOrder.value = updated
      }
    }

    onMounted(loadData)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      recommendations,
      orderError,
      successMessage,
      lastOrder,
      selectedItems,
      totalCost,
      remainingBudget,
      overBudget,
      estimatedLeadTime,
      canPlaceOrder,
      updateQuantity,
      placeOrder,
      syncOrder
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.card-subtitle {
  font-size: 0.813rem;
  color: #64748b;
}

.budget-card {
  padding-bottom: 1.5rem;
}

.budget-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  accent-color: #2563eb;
  cursor: pointer;
  margin: 0.5rem 0;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 1.25rem;
}

.budget-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.summary-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-value.danger {
  color: #dc2626;
}

.recommend-table {
  table-layout: fixed;
  width: 100%;
}

.col-select {
  width: 40px;
}

.row-disabled {
  opacity: 0.5;
}

.qty-input {
  width: 90px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.qty-input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.order-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.order-error {
  width: 100%;
  margin: 0;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-confirmation {
  border-left: 4px solid #2563eb;
}

.confirmation-message {
  color: #334155;
  font-size: 0.938rem;
  margin-bottom: 1rem;
}

.confirmation-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.detail-value {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
}

.sync-btn {
  background: white;
  color: #2563eb;
  border: 1px solid #2563eb;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.sync-btn:hover {
  background: #eff6ff;
}
</style>
