<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Recommend items to restock based on demand forecasts and your available budget.</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <span class="card-title">Budget</span>
      </div>
      <div class="budget-body">
        <div class="slider-row">
          <label class="slider-label">Available Budget</label>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          min="10000"
          max="500000"
          step="5000"
          class="budget-slider"
        />
        <div class="slider-bounds">
          <span>{{ formatCurrency(10000) }}</span>
          <span>{{ formatCurrency(500000) }}</span>
        </div>
        <div class="remaining-row">
          <span class="remaining-label">Remaining Budget</span>
          <span :class="['remaining-value', remainingBudget >= 0 ? 'positive' : 'negative']">
            {{ formatCurrency(remainingBudget) }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="successMessage" class="success-banner">
      {{ successMessage }}
    </div>

    <div v-if="submitError" class="error submit-error">
      {{ submitError }}
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">Recommended Items</span>
        <span class="selection-summary">
          {{ selectedItems.length }} item{{ selectedItems.length !== 1 ? 's' : '' }} selected
          &nbsp;&middot;&nbsp;
          Est. total: {{ formatCurrency(totalCost) }}
        </span>
      </div>

      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="restockItems.length === 0" class="empty-state">
        No restocking recommendations available.
      </div>
      <div v-else>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-checkbox"></th>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Current Demand</th>
                <th>Forecasted Demand</th>
                <th>Unit Cost</th>
                <th>Est. Order Cost</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in restockItems" :key="item.sku">
                <td class="col-checkbox">
                  <input
                    type="checkbox"
                    :checked="item.selected"
                    @change="toggleItem(item)"
                  />
                </td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>{{ item.current_demand.toLocaleString() }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ formatCurrency(item.est_cost) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="actions-row">
          <button
            class="place-order-btn"
            :disabled="selectedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
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
    const { currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory } = useFilters()

    const loading = ref(false)
    const error = ref(null)
    const restockItems = ref([])
    const budget = ref(100000)
    const submitting = ref(false)
    const successMessage = ref(null)
    const submitError = ref(null)

    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', { style: 'currency', currency: currentCurrency.value })
    }

    const selectedItems = computed(() => restockItems.value.filter(i => i.selected))
    const totalCost = computed(() => selectedItems.value.reduce((sum, i) => sum + i.est_cost, 0))
    const remainingBudget = computed(() => budget.value - totalCost.value)

    const runGreedy = () => {
      const sorted = restockItems.value.slice().sort((a, b) => {
        return (b.forecasted_demand - b.current_demand) - (a.forecasted_demand - a.current_demand)
      })

      let running = 0
      const selectedSkus = new Set()
      for (const item of sorted) {
        if (running + item.est_cost <= budget.value) {
          running += item.est_cost
          selectedSkus.add(item.sku)
        }
      }

      restockItems.value = restockItems.value.map(item => ({
        ...item,
        selected: selectedSkus.has(item.sku)
      }))
    }

    const toggleItem = (item) => {
      restockItems.value = restockItems.value.map(i =>
        i.sku === item.sku ? { ...i, selected: !i.selected } : i
      )
    }

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecasts, inventoryItems] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: selectedLocation.value,
            category: selectedCategory.value
          })
        ])

        const inventoryMap = {}
        for (const inv of inventoryItems) {
          inventoryMap[inv.sku] = inv
        }

        restockItems.value = forecasts
          .filter(f => inventoryMap[f.item_sku] != null)
          .map(f => ({
            sku: f.item_sku,
            name: f.item_name,
            current_demand: f.current_demand,
            forecasted_demand: f.forecasted_demand,
            trend: f.trend,
            period: f.period,
            unit_cost: inventoryMap[f.item_sku].unit_cost,
            est_cost: f.forecasted_demand * inventoryMap[f.item_sku].unit_cost,
            selected: false
          }))

        runGreedy()
      } catch (err) {
        error.value = 'Failed to load restocking data'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    watch(budget, runGreedy, { immediate: false })
    watch([selectedLocation, selectedCategory], loadData)

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      successMessage.value = null
      try {
        const order = await api.createRestockingOrder({
          items: selectedItems.value.map(i => ({
            sku: i.sku,
            name: i.name,
            quantity: i.forecasted_demand,
            unit_cost: i.unit_cost
          })),
          budget: budget.value
        })
        successMessage.value = `Order ${order.order_number} placed successfully.`
        runGreedy()
      } catch (err) {
        submitError.value = 'Failed to place order. Please try again.'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      restockItems,
      budget,
      submitting,
      successMessage,
      submitError,
      selectedItems,
      totalCost,
      remainingBudget,
      formatCurrency,
      toggleItem,
      placeOrder
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.budget-card {
  margin-bottom: 1.5rem;
}

.budget-body {
  padding: 1.25rem 1.5rem;
}

.slider-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.slider-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.budget-value {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.remaining-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.remaining-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.remaining-value {
  font-size: 1rem;
  font-weight: 600;
}

.remaining-value.positive {
  color: #16a34a;
}

.remaining-value.negative {
  color: #dc2626;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.submit-error {
  margin-bottom: 1.5rem;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
}

.loading,
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.error {
  color: #ef4444;
  font-size: 0.875rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.selection-summary {
  font-size: 0.875rem;
  color: #64748b;
}

.col-checkbox {
  width: 2.5rem;
  text-align: center;
}

.actions-row {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.place-order-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
