<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Control Card -->
    <div class="card">
      <div class="budget-header">
        <span class="card-title">{{ t('restocking.budgetLabel') }}</span>
        <span class="budget-value">{{ currencySymbol }}{{ formatCurrency(budget) }}</span>
      </div>

      <input
        type="range"
        min="0"
        max="50000"
        step="500"
        v-model.number="budget"
        class="budget-slider"
      />

      <div class="budget-range-hint">
        <span>{{ currencySymbol }} 0</span>
        <span>{{ currencySymbol }} 50,000</span>
      </div>

      <div class="budget-summary">
        <div class="summary-item">
          <div class="summary-label">{{ t('restocking.totalCost') }}</div>
          <div class="summary-value">{{ currencySymbol }}{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="summary-value" :style="{ color: remainingBudget < 0 ? '#dc2626' : '#0f172a' }">
            {{ currencySymbol }}{{ formatCurrency(remainingBudget) }}
          </div>
        </div>
        <div class="summary-item">
          <div class="summary-label">{{ t('restocking.recommendedItems') }}</div>
          <div class="summary-value">{{ recommendedItems.length }}</div>
        </div>
      </div>

      <button
        class="place-order-btn"
        :disabled="submitting || recommendedItems.length === 0"
        @click="placeOrder"
      >
        {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
      </button>

      <div v-if="submitSuccess" class="success-banner">
        {{ t('restocking.orderPlaced') }}
      </div>

      <div v-if="error" class="error-banner">
        {{ error }}
      </div>
    </div>

    <!-- Recommendations Table Card -->
    <div class="card">
      <div class="card-header">
        <div class="recommendations-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
          <span class="count-badge">{{ recommendedItems.length }}</span>
        </div>
      </div>

      <div v-if="loading">{{ t('common.loading') }}</div>
      <div v-else-if="recommendedItems.length === 0" class="no-recommendations">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else class="table-container">
        <table class="recommendations-table">
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.quantityToOrder') }}</th>
              <th>{{ t('restocking.table.totalCost') }}</th>
              <th>{{ t('restocking.table.belowReorder') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendedItems" :key="item.sku">
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ item.name }}</td>
              <td>
                <span :class="['badge', item.trend]">{{ t('trends.' + item.trend) }}</span>
              </td>
              <td>{{ currencySymbol }}{{ formatCurrency(item.unit_cost) }}</td>
              <td>{{ item.quantity_to_order }}</td>
              <td>{{ currencySymbol }}{{ formatCurrency(item.item_total_cost) }}</td>
              <td>
                <span v-if="item.is_below_reorder_point" class="badge danger">
                  {{ t('restocking.belowReorder') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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
    const { t, currencySymbol } = useI18n()
    const { selectedLocation, selectedCategory } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitSuccess = ref(false)
    const budget = ref(10000)
    const allForecasts = ref([])
    const allInventory = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        allForecasts.value = forecastsData
        allInventory.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    onMounted(loadData)

    const enrichedCandidates = computed(() => {
      const inventoryBySku = {}
      for (const inv of allInventory.value) {
        inventoryBySku[inv.sku] = inv
      }

      const result = []
      for (const forecast of allForecasts.value) {
        const inv = inventoryBySku[forecast.item_sku]
        if (!inv) continue

        const quantity_to_order = Math.max(1, forecast.forecasted_demand - inv.quantity_on_hand)
        const item_total_cost = quantity_to_order * inv.unit_cost

        if (item_total_cost <= 0) continue

        result.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          trend: forecast.trend,
          unit_cost: inv.unit_cost,
          quantity_on_hand: inv.quantity_on_hand,
          reorder_point: inv.reorder_point,
          is_below_reorder_point: inv.quantity_on_hand <= inv.reorder_point,
          quantity_to_order,
          item_total_cost
        })
      }
      return result
    })

    const sortedCandidates = computed(() => {
      return [...enrichedCandidates.value].sort((a, b) => {
        // Tier 1: increasing trend first
        const trendA = a.trend === 'increasing' ? 0 : 1
        const trendB = b.trend === 'increasing' ? 0 : 1
        if (trendA !== trendB) return trendA - trendB

        // Tier 2: below reorder point first
        const reorderA = a.is_below_reorder_point ? 0 : 1
        const reorderB = b.is_below_reorder_point ? 0 : 1
        if (reorderA !== reorderB) return reorderA - reorderB

        // Tier 3: highest units per dollar (descending)
        return (1 / b.unit_cost) - (1 / a.unit_cost)
      })
    })

    const recommendedItems = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const candidate of sortedCandidates.value) {
        if (candidate.item_total_cost <= remaining) {
          selected.push(candidate)
          remaining -= candidate.item_total_cost
        }
      }
      return selected
    })

    const totalCost = computed(() =>
      recommendedItems.value.reduce((sum, item) => sum + item.item_total_cost, 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const formatCurrency = (value) => {
      return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0) return
      if (!confirm(t('restocking.confirmOrder'))) return

      submitting.value = true
      error.value = null

      try {
        const now = new Date()
        const delivery = new Date(now)
        delivery.setDate(delivery.getDate() + 7)

        await api.createRestockingOrder({
          items: recommendedItems.value.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.quantity_to_order,
            unit_cost: item.unit_cost,
            total_cost: item.item_total_cost,
            trend: item.trend,
            is_below_reorder_point: item.is_below_reorder_point
          })),
          budget: budget.value,
          total_cost: totalCost.value,
          submitted_at: now.toISOString(),
          expected_delivery: delivery.toISOString()
        })

        submitSuccess.value = true
        setTimeout(() => { submitSuccess.value = false }, 4000)
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    return {
      t,
      loading,
      error,
      submitting,
      submitSuccess,
      budget,
      recommendedItems,
      totalCost,
      remainingBudget,
      currencySymbol,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 2rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
  margin: 0.75rem 0;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-range-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  display: flex;
  justify-content: space-between;
}

.budget-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 1.25rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.summary-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-weight: 500;
  font-size: 0.875rem;
  margin-top: 1rem;
}

.error-banner {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  margin-top: 1rem;
}

.recommendations-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.count-badge {
  background: #e2e8f0;
  color: #475569;
  border-radius: 9999px;
  padding: 0.125rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.no-recommendations {
  text-align: center;
  color: #64748b;
  padding: 2rem;
  font-size: 0.875rem;
}

.recommendations-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.recommendations-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
}

.recommendations-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
  vertical-align: middle;
}

.recommendations-table tbody tr:last-child td {
  border-bottom: none;
}

.recommendations-table tbody tr:hover {
  background: #f8fafc;
}

.table-container {
  overflow-x: auto;
}
</style>
