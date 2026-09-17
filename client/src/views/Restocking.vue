<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set your budget and get recommendations for items that need restocking.</p>
    </div>

    <div v-if="loading" class="loading">Loading inventory data...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="orderPlaced" class="success-banner">
        <div class="success-icon">✓</div>
        <div class="success-content">
          <strong>Order placed successfully!</strong>
          <p>Your restocking order has been submitted and will be delivered in 7 days.</p>
        </div>
        <button class="btn-reset" @click="resetOrder">Place Another Order</button>
      </div>

      <div class="budget-card card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-body">
          <div class="budget-display">
            <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
            <span class="budget-label">budget</span>
          </div>
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="100000"
            step="1000"
            class="budget-slider"
          />
          <div class="budget-marks">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}25k</span>
            <span>{{ currencySymbol }}50k</span>
            <span>{{ currencySymbol }}75k</span>
            <span>{{ currencySymbol }}100k</span>
          </div>
          <div class="budget-summary" v-if="selectedItems.length > 0">
            <div class="budget-stat">
              <span class="stat-label">Total Cost</span>
              <span class="stat-val cost">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</span>
            </div>
            <div class="budget-stat">
              <span class="stat-label">Remaining</span>
              <span class="stat-val" :class="remainingBudget < 0 ? 'over' : 'remaining'">
                {{ currencySymbol }}{{ remainingBudget.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card" v-if="selectedItems.length > 0 || lowStockItems.length === 0">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Items
            <span class="item-count">({{ selectedItems.length }} items)</span>
          </h3>
          <p class="card-subtitle" v-if="lowStockItems.length > selectedItems.length">
            {{ lowStockItems.length - selectedItems.length }} item(s) not included — increase budget to cover them.
          </p>
        </div>

        <div v-if="lowStockItems.length === 0" class="empty-state">
          <p>All inventory items are well-stocked. No restocking needed at this time.</p>
        </div>

        <div v-else-if="selectedItems.length === 0" class="empty-state">
          <p>Budget is too low to restock any items. Increase the slider to see recommendations.</p>
        </div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Warehouse</th>
                <th class="num-col">In Stock</th>
                <th class="num-col">Reorder Point</th>
                <th class="num-col">Qty to Order</th>
                <th class="num-col">Unit Cost</th>
                <th class="num-col">Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedItems" :key="item.sku">
                <td><code class="sku">{{ item.sku }}</code></td>
                <td>{{ item.name }}</td>
                <td>{{ item.warehouse }}</td>
                <td class="num-col">{{ item.quantity_on_hand }}</td>
                <td class="num-col">{{ item.reorder_point }}</td>
                <td class="num-col">
                  <input
                    type="number"
                    v-model.number="item.orderQty"
                    :min="1"
                    class="qty-input"
                  />
                </td>
                <td class="num-col">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td class="num-col"><strong>{{ currencySymbol }}{{ (item.orderQty * item.unit_cost).toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer" v-if="selectedItems.length > 0">
          <div class="footer-summary">
            <span>{{ selectedItems.length }} items &nbsp;·&nbsp; Total: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</strong></span>
          </div>
          <button
            class="place-order-btn"
            :disabled="placing || totalCost <= 0"
            @click="placeOrder"
          >
            <span v-if="placing">Placing Order...</span>
            <span v-else>Place Order</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const orderPlaced = ref(false)

    const budget = ref(10000)
    const inventoryItems = ref([])

    // Items below reorder point, sorted by shortage ratio descending
    const lowStockItems = computed(() => {
      return inventoryItems.value
        .filter(item => item.quantity_on_hand < item.reorder_point)
        .map(item => ({
          ...item,
          shortage: item.reorder_point - item.quantity_on_hand,
          priorityScore: (item.reorder_point - item.quantity_on_hand) / item.reorder_point
        }))
        .sort((a, b) => b.priorityScore - a.priorityScore)
    })

    // Greedy selection within budget, each item gets an editable orderQty
    const selectedItems = ref([])

    function buildRecommendations() {
      const result = []
      let remaining = budget.value
      for (const item of lowStockItems.value) {
        const unitCost = item.unit_cost
        if (unitCost <= 0) continue
        const maxQty = Math.floor(remaining / unitCost)
        if (maxQty <= 0) continue
        const qty = Math.min(item.shortage, maxQty)
        result.push({ ...item, orderQty: qty })
        remaining -= qty * unitCost
      }
      selectedItems.value = result
    }

    watch(budget, buildRecommendations)

    const totalCost = computed(() =>
      selectedItems.value.reduce((sum, item) => sum + item.orderQty * item.unit_cost, 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    async function placeOrder() {
      placing.value = true
      try {
        const items = selectedItems.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.orderQty,
          unit_price: item.unit_cost
        }))
        await api.createRestockingOrder({
          items,
          total_value: parseFloat(totalCost.value.toFixed(2))
        })
        orderPlaced.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    function resetOrder() {
      orderPlaced.value = false
      buildRecommendations()
    }

    onMounted(async () => {
      try {
        inventoryItems.value = await api.getInventory()
        buildRecommendations()
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    })

    return {
      loading, error, placing, orderPlaced,
      budget, currencySymbol,
      lowStockItems, selectedItems,
      totalCost, remainingBudget,
      placeOrder, resetOrder
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.25rem;
}

.page-header p {
  color: #64748b;
  margin: 0;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.success-icon {
  width: 2rem;
  height: 2rem;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.success-content {
  flex: 1;
}

.success-content strong {
  color: #166534;
  display: block;
}

.success-content p {
  color: #15803d;
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
}

.btn-reset {
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
}

.btn-reset:hover {
  background: #059669;
}

.budget-card {
  margin-bottom: 1.5rem;
}

.budget-body {
  padding: 1rem 1.25rem 1.25rem;
}

.budget-display {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-marks {
  display: flex;
  justify-content: space-between;
  color: #94a3b8;
  font-size: 0.75rem;
  margin-top: 0.5rem;
}

.budget-summary {
  display: flex;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.budget-stat .stat-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-stat .stat-val {
  font-size: 1.125rem;
  font-weight: 600;
}

.stat-val.cost { color: #0f172a; }
.stat-val.remaining { color: #10b981; }
.stat-val.over { color: #ef4444; }

.card-subtitle {
  font-size: 0.8rem;
  color: #f59e0b;
  margin: 0;
}

.item-count {
  font-size: 0.875rem;
  font-weight: 400;
  color: #64748b;
  margin-left: 0.25rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.restock-table {
  width: 100%;
  border-collapse: collapse;
}

.restock-table th,
.restock-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
}

.restock-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.restock-table tr:last-child td {
  border-bottom: none;
}

.restock-table tr:hover td {
  background: #f8fafc;
}

.num-col {
  text-align: right !important;
}

.sku {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #475569;
}

.qty-input {
  width: 70px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: right;
  font-size: 0.875rem;
  color: #0f172a;
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 0 0 12px 12px;
}

.footer-summary {
  font-size: 0.875rem;
  color: #475569;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

.error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  padding: 1rem;
  color: #dc2626;
}
</style>
