<!-- ABOUTME: Restocking view that converts backlog shortfalls into restock orders -->
<!-- ABOUTME: Includes budget slider for greedy auto-selection and order placement UI -->
<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Review backlog shortfalls and generate restock orders within budget.</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Restocking Budget</h3>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="slider-row">
          <span class="slider-bound">{{ formatCurrency(0) }}</span>
          <input
            type="range"
            class="budget-slider"
            :min="0"
            :max="totalCost"
            :step="1000"
            v-model.number="budget"
          />
          <span class="slider-bound slider-bound-max">{{ formatCurrency(totalCost) }}</span>
        </div>
        <p class="slider-hint">Items are auto-selected in priority order until the budget is reached.</p>
      </div>

      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      <div v-if="orderError" class="error">{{ orderError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
        </div>
        <div v-if="recommendations.length === 0" class="empty-state">
          No restocking candidates found for the current filters.
        </div>
        <div v-else>
          <div class="table-container">
            <table class="restock-table">
              <thead>
                <tr>
                  <th class="col-priority">Priority</th>
                  <th class="col-name">Item Name</th>
                  <th class="col-sku">SKU</th>
                  <th class="col-shortfall">Shortfall</th>
                  <th class="col-trend">Demand Trend</th>
                  <th class="col-unit-cost">Unit Cost</th>
                  <th class="col-total">Est. Total</th>
                  <th class="col-select">Select</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="rec in recommendations"
                  :key="rec.item_sku"
                  :class="{ 'row-selected': isSelected(rec.item_sku) }"
                >
                  <td class="col-priority">
                    <span :class="['badge', rec.priority]">{{ rec.priority }}</span>
                  </td>
                  <td class="col-name">{{ rec.item_name }}</td>
                  <td class="col-sku"><strong>{{ rec.item_sku }}</strong></td>
                  <td class="col-shortfall">{{ rec.quantity_to_order }}</td>
                  <td class="col-trend">
                    <span v-if="rec.trend" :class="['badge', rec.trend]">{{ rec.trend }}</span>
                    <span v-else class="muted">—</span>
                  </td>
                  <td class="col-unit-cost">{{ formatCurrency(rec.unit_cost) }}</td>
                  <td class="col-total"><strong>{{ formatCurrency(rec.estimated_cost) }}</strong></td>
                  <td class="col-select">
                    <input
                      type="checkbox"
                      :checked="isSelected(rec.item_sku)"
                      @change="toggleSelection(rec.item_sku)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="table-footer">
            <span class="selected-summary">
              Selected total: <strong>{{ formatCurrency(selectedTotal) }}</strong>
              &mdash; {{ selectedItems.length }} item{{ selectedItems.length !== 1 ? 's' : '' }}
            </span>
            <button
              class="btn-primary"
              :disabled="selectedItems.length === 0 || submitting"
              @click="placeOrder"
            >
              {{ submitting ? 'Placing Order...' : 'Place Order' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const successMessage = ref(null)
    const orderError = ref(null)
    const submitting = ref(false)

    const backlogItems = ref([])
    const inventoryItems = ref([])
    const forecasts = ref([])

    const budget = ref(0)
    const selectedSkus = ref(new Set())

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const priorityOrder = { high: 0, medium: 1, low: 2 }

    const recommendations = computed(() => {
      const invMap = new Map(inventoryItems.value.map(i => [i.sku, i]))
      const forecastMap = new Map(forecasts.value.map(f => [f.item_sku, f]))

      return backlogItems.value
        .map(b => {
          const inv = invMap.get(b.item_sku) || null
          const forecast = forecastMap.get(b.item_sku) || null
          const unit_cost = inv ? inv.unit_cost : 0
          const quantity_to_order = Math.max(0, b.quantity_needed - b.quantity_available)
          const estimated_cost = quantity_to_order * unit_cost

          return {
            ...b,
            unit_cost,
            warehouse: inv ? inv.warehouse : null,
            category: inv ? inv.category : null,
            trend: forecast ? forecast.trend : null,
            quantity_to_order,
            estimated_cost
          }
        })
        .filter(r => r.quantity_to_order > 0)
        .sort((a, b) => {
          const pDiff = (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3)
          if (pDiff !== 0) return pDiff
          return b.days_delayed - a.days_delayed
        })
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, r) => sum + r.estimated_cost, 0)
    })

    const selectedItems = computed(() => {
      return recommendations.value.filter(r => selectedSkus.value.has(r.item_sku))
    })

    const selectedTotal = computed(() => {
      return selectedItems.value.reduce((sum, r) => sum + r.estimated_cost, 0)
    })

    const updateSelectionFromBudget = () => {
      const selected = new Set()
      let remaining = budget.value
      for (const rec of recommendations.value) {
        if (rec.estimated_cost <= remaining) {
          selected.add(rec.item_sku)
          remaining -= rec.estimated_cost
        }
      }
      selectedSkus.value = selected
    }

    watch(budget, updateSelectionFromBudget)

    const isSelected = (sku) => selectedSkus.value.has(sku)

    const toggleSelection = (sku) => {
      const newSet = new Set(selectedSkus.value)
      if (newSet.has(sku)) {
        newSet.delete(sku)
      } else {
        newSet.add(sku)
      }
      selectedSkus.value = newSet
    }

    const formatCurrency = (value) => {
      return currencySymbol.value + Math.round(value).toLocaleString()
    }

    const loadData = async () => {
      loading.value = true
      error.value = null
      successMessage.value = null
      try {
        const filters = getCurrentFilters()
        const [backlogData, inventoryData, forecastData] = await Promise.all([
          api.getBacklog(),
          api.getInventory({ warehouse: filters.warehouse, category: filters.category }),
          api.getDemandForecasts()
        ])
        backlogItems.value = backlogData
        inventoryItems.value = inventoryData
        forecasts.value = forecastData
        // Set budget to total cost of all candidates and auto-select all
        budget.value = totalCost.value
        updateSelectionFromBudget()
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return

      submitting.value = true
      orderError.value = null
      successMessage.value = null

      try {
        await api.createOrder({
          customer: 'Internal Restocking',
          items: selectedItems.value.map(r => ({
            sku: r.item_sku,
            name: r.item_name,
            quantity: r.quantity_to_order,
            unit_price: r.unit_cost
          })),
          warehouse: selectedLocation.value !== 'all' ? selectedLocation.value : null,
          category: selectedCategory.value !== 'all' ? selectedCategory.value : null
        })
        successMessage.value = 'Order submitted successfully'
        selectedSkus.value = new Set()
        await loadData()
      } catch (err) {
        orderError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      successMessage,
      orderError,
      submitting,
      recommendations,
      totalCost,
      budget,
      selectedItems,
      selectedTotal,
      isSelected,
      toggleSelection,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card .card-header {
  align-items: center;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 0.75rem 0;
}

.slider-bound {
  font-size: 0.875rem;
  color: #64748b;
  white-space: nowrap;
  min-width: 80px;
}

.slider-bound-max {
  text-align: right;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-hint {
  font-size: 0.813rem;
  color: #64748b;
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-priority { width: 100px; }
.col-name { width: 200px; }
.col-sku { width: 130px; }
.col-shortfall { width: 90px; }
.col-trend { width: 120px; }
.col-unit-cost { width: 100px; }
.col-total { width: 110px; }
.col-select { width: 70px; text-align: center; }

.row-selected {
  background: #eff6ff;
}

tbody tr.row-selected:hover {
  background: #dbeafe;
}

.muted {
  color: #94a3b8;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.selected-summary {
  font-size: 0.938rem;
  color: #64748b;
}

.selected-summary strong {
  color: #0f172a;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
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

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}
</style>
