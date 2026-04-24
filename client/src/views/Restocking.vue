<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget slider card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetAllocation') }}</h3>
        </div>
        <div class="budget-row">
          <div class="budget-stat">
            <span class="budget-label">{{ t('restocking.budget') }}</span>
            <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-label">{{ t('restocking.allocated') }}</span>
            <span class="budget-value allocated">{{ currencySymbol }}{{ totalAllocated.toLocaleString() }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-label">{{ t('restocking.remaining') }}</span>
            <span class="budget-value remaining" :class="{ negative: (budget - totalAllocated) <= 0 }">{{ currencySymbol }}{{ (budget - totalAllocated).toLocaleString() }}</span>
          </div>
        </div>
        <input
          type="range"
          min="1000"
          max="50000"
          step="500"
          v-model.number="budget"
        />
        <div class="range-labels">
          <span>{{ currencySymbol }}1,000</span>
          <span>{{ currencySymbol }}50,000</span>
        </div>
      </div>

      <!-- Stats (only when lowStockItems.length > 0) -->
      <div class="stats-grid" v-if="lowStockItems.length > 0">
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.itemsBelowReorder') }}</div>
          <div class="stat-value">{{ lowStockItems.length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalRestockCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalRecommendedCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.itemsInBudget') }}</div>
          <div class="stat-value">{{ itemsInBudget.length }}</div>
        </div>
      </div>

      <!-- noLowStock message OR recommendations table -->
      <div v-if="lowStockItems.length === 0" class="card">
        <p>{{ t('restocking.noLowStock') }}</p>
      </div>
      <div v-else class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
            :disabled="itemsInBudget.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="orderSubmitted" class="success-banner">
          {{ t('restocking.orderSuccess').replace('{orderNumber}', lastOrderNumber) }}
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.priority') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.currentQty') }}</th>
                <th>{{ t('restocking.table.reorderPoint') }}</th>
                <th>{{ t('restocking.table.deficit') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.estimatedCost') }}</th>
                <th>{{ t('restocking.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, index) in recommendations"
                :key="item.sku"
                :class="{ 'row-over-budget': item.allocatedQty === 0 }"
              >
                <td><span class="priority-num">{{ index + 1 }}</span></td>
                <td>{{ item.sku }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.reorder_point }}</td>
                <td>{{ item.deficit }}</td>
                <td>{{ item.allocatedQty }}</td>
                <td>{{ currencySymbol }}{{ (item.allocatedQty * item.unit_cost).toLocaleString() }}</td>
                <td>
                  <span v-if="item.status === 'within-budget'" class="badge success">{{ t('restocking.withinBudget') }}</span>
                  <span v-else-if="item.status === 'partial'" class="badge warning">{{ t('restocking.partial') }}</span>
                  <span v-else class="badge danger">{{ t('restocking.overBudget') }}</span>
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
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const inventoryItems = ref([])
    const budget = ref(10000)
    const submitting = ref(false)
    const orderSubmitted = ref(false)
    const lastOrderNumber = ref('')

    const loadInventory = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        inventoryItems.value = await api.getInventory(filters)
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const lowStockItems = computed(() => {
      return inventoryItems.value.filter(item => item.quantity_on_hand <= item.reorder_point)
    })

    const sortedLowStockItems = computed(() => {
      return [...lowStockItems.value].map(item => {
        const deficit = item.reorder_point - item.quantity_on_hand
        const buffer = Math.ceil(item.reorder_point * 0.20)
        const recommendedQty = deficit + buffer
        const urgencyScore = (deficit / item.reorder_point) * 100
        return { ...item, deficit, buffer, recommendedQty, urgencyScore }
      }).sort((a, b) => b.urgencyScore - a.urgencyScore)
    })

    const recommendations = computed(() => {
      let remaining = budget.value
      return sortedLowStockItems.value.map(item => {
        const fullCost = item.recommendedQty * item.unit_cost
        let allocatedQty = 0
        let status = 'over-budget'

        if (remaining >= fullCost) {
          allocatedQty = item.recommendedQty
          remaining -= fullCost
          status = 'within-budget'
        } else if (remaining >= item.unit_cost) {
          allocatedQty = Math.floor(remaining / item.unit_cost)
          remaining -= allocatedQty * item.unit_cost
          status = 'partial'
        } else {
          allocatedQty = 0
          status = 'over-budget'
        }

        return { ...item, allocatedQty, status }
      })
    })

    const totalAllocated = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.allocatedQty * item.unit_cost, 0)
    })

    const totalRecommendedCost = computed(() => {
      return sortedLowStockItems.value.reduce((sum, item) => sum + item.recommendedQty * item.unit_cost, 0)
    })

    const itemsInBudget = computed(() => {
      return recommendations.value.filter(item => item.allocatedQty > 0)
    })

    const placeOrder = async () => {
      if (itemsInBudget.value.length === 0) return
      try {
        submitting.value = true
        const result = await api.submitRestockingOrder({
          items: itemsInBudget.value.map(item => ({
            inventory_item_id: item.id,
            sku: item.sku,
            name: item.name,
            quantity: item.allocatedQty,
            unit_cost: item.unit_cost
          })),
          total_budget: budget.value
        })
        lastOrderNumber.value = result.order_number
        orderSubmitted.value = true
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      orderSubmitted.value = false
      loadInventory()
    })

    onMounted(loadInventory)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      lowStockItems,
      recommendations,
      totalAllocated,
      totalRecommendedCost,
      itemsInBudget,
      submitting,
      orderSubmitted,
      lastOrderNumber,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-value.allocated {
  color: #2563eb;
}

.budget-value.remaining {
  color: #059669;
}

.budget-value.remaining.negative {
  color: #dc2626;
}

input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 4px;
  accent-color: #2563eb;
  cursor: pointer;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  border-radius: 8px;
  padding: 0.875rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.row-over-budget td {
  opacity: 0.45;
  cursor: not-allowed;
}

.priority-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f1f5f9;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
}
</style>
