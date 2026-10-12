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
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.setBudget') }}</h3>
        </div>
        <BudgetSlider
          v-model="budgetAmount"
          :min="0"
          :max="maxBudget"
          :step="1000"
          :label="t('restocking.budgetLabel')"
        />
      </div>

      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ displayedRecommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(selectedSummary.totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrency(budgetAmount - selectedSummary.totalCost) }}</div>
        </div>
      </div>

      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations') }} ({{ displayedRecommendations.length }})
          </h3>
        </div>

        <div v-if="displayedRecommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th class="col-checkbox"></th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-category">{{ t('restocking.table.category') }}</th>
                <th class="col-stock">{{ t('restocking.table.stock') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-unit-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-total">{{ t('restocking.table.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in displayedRecommendations" :key="rec.sku">
                <td class="col-checkbox">
                  <input
                    type="checkbox"
                    :checked="selectedItems.has(rec.sku)"
                    @change="toggleItem(rec.sku)"
                    class="checkbox-input"
                  />
                </td>
                <td class="col-sku"><strong>{{ rec.sku }}</strong></td>
                <td class="col-name">{{ translateProductName(rec.name) }}</td>
                <td class="col-category">{{ rec.category }}</td>
                <td class="col-stock">
                  <div class="stock-info">
                    <span>{{ rec.currentStock }} / {{ rec.reorderPoint }}</span>
                  </div>
                </td>
                <td class="col-trend">
                  <span :class="['badge', getTrendClass(rec.trend)]">
                    {{ t(`restocking.trends.${rec.trend}`) }}
                  </span>
                </td>
                <td class="col-qty">{{ rec.recommendedQty }}</td>
                <td class="col-unit-cost">{{ formatCurrency(rec.unitCost) }}</td>
                <td class="col-total"><strong>{{ formatCurrency(rec.totalCost) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Submit Section -->
      <div v-if="displayedRecommendations.length > 0" class="submit-section">
        <div class="summary">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.selectedItems') }}:</span>
            <span class="summary-value">{{ selectedSummary.count }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.totalOrderCost') }}:</span>
            <span class="summary-value">{{ formatCurrency(selectedSummary.totalCost) }}</span>
          </div>
        </div>
        <button
          :disabled="!canSubmit"
          @click="submitRestockingOrder"
          class="submit-button"
        >
          {{ submitting ? t('restocking.submitting') : t('restocking.submitOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import BudgetSlider from '../components/BudgetSlider.vue'

export default {
  name: 'Restocking',
  components: {
    BudgetSlider
  },
  setup() {
    const router = useRouter()
    const { getCurrentFilters, selectedLocation, selectedCategory } = useFilters()
    const { t, currentCurrency, translateProductName } = useI18n()

    const budgetAmount = ref(50000)
    const maxBudget = ref(100000)
    const demandForecasts = ref([])
    const inventoryItems = ref([])
    const selectedItems = ref(new Set())
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const formatCurrency = (value) => {
      return `${currencySymbol.value}${value.toLocaleString()}`
    }

    // Join demand forecasts with inventory and calculate priority
    const recommendations = computed(() => {
      const recs = []

      for (const forecast of demandForecasts.value) {
        const inventoryItem = inventoryItems.value.find(item => item.sku === forecast.sku)
        if (!inventoryItem) continue

        const quantityOnHand = inventoryItem.quantity_on_hand
        const reorderPoint = inventoryItem.reorder_point

        // Filter: only items where quantity_on_hand <= reorder_point * 1.5
        if (quantityOnHand > reorderPoint * 1.5) continue

        // Calculate priority score
        const stockRatio = quantityOnHand / reorderPoint
        const demandIncrease = (forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand
        const trendWeight = forecast.trend === 'increasing' ? 2 : (forecast.trend === 'stable' ? 1 : 0.5)
        const priorityScore = (2 - stockRatio) * trendWeight * (1 + demandIncrease)

        // Calculate recommended quantity
        const shortage = Math.max(0, reorderPoint * 2 - quantityOnHand)
        const demandBuffer = Math.max(0, forecast.forecasted_demand - quantityOnHand)
        const recommendedQty = Math.max(shortage, demandBuffer, 1)

        // Calculate total cost
        const unitCost = inventoryItem.unit_cost
        const totalCost = recommendedQty * unitCost

        recs.push({
          sku: forecast.sku,
          name: inventoryItem.name,
          category: inventoryItem.category,
          warehouse: inventoryItem.warehouse,
          currentStock: quantityOnHand,
          reorderPoint: reorderPoint,
          forecastedDemand: forecast.forecasted_demand,
          trend: forecast.trend,
          recommendedQty: recommendedQty,
          unitCost: unitCost,
          totalCost: totalCost,
          priorityScore: priorityScore
        })
      }

      // Sort by priority score descending
      return recs.sort((a, b) => b.priorityScore - a.priorityScore)
    })

    // SKUs that fit within budget
    const affordableRecommendations = computed(() => {
      const affordable = []
      let accumulatedCost = 0

      for (const rec of recommendations.value) {
        if (accumulatedCost + rec.totalCost <= budgetAmount.value) {
          affordable.push(rec.sku)
          accumulatedCost += rec.totalCost
        }
      }

      return affordable
    })

    // Filter recommendations to show only affordable ones
    const displayedRecommendations = computed(() => {
      return recommendations.value.filter(rec => affordableRecommendations.value.includes(rec.sku))
    })

    // Calculate total for selected items
    const selectedSummary = computed(() => {
      const selectedRecs = recommendations.value.filter(rec => selectedItems.value.has(rec.sku))
      return {
        count: selectedRecs.length,
        totalCost: selectedRecs.reduce((sum, rec) => sum + rec.totalCost, 0)
      }
    })

    // Validation for submit button
    const canSubmit = computed(() => {
      return selectedItems.value.size > 0 &&
             selectedSummary.value.totalCost <= budgetAmount.value &&
             !submitting.value
    })

    // Auto-select affordable items when budget or recommendations change
    watch([budgetAmount, recommendations], () => {
      selectedItems.value = new Set(affordableRecommendations.value)
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        const filters = getCurrentFilters()
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        demandForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
        console.error('Load error:', err)
      } finally {
        loading.value = false
      }
    }

    const toggleItem = (sku) => {
      const newSet = new Set(selectedItems.value)
      if (newSet.has(sku)) {
        newSet.delete(sku)
      } else {
        newSet.add(sku)
      }
      selectedItems.value = newSet
    }

    const submitRestockingOrder = async () => {
      try {
        submitting.value = true

        // Calculate delivery date (today + 7 days)
        const deliveryDate = new Date()
        deliveryDate.setDate(deliveryDate.getDate() + 7)

        // Build items array from selections
        const selectedRecs = recommendations.value.filter(rec => selectedItems.value.has(rec.sku))
        const items = selectedRecs.map(rec => ({
          sku: rec.sku,
          name: rec.name,
          quantity: rec.recommendedQty,
          unit_price: rec.unitCost
        }))

        // Determine primary warehouse/category
        const primaryWarehouse = selectedRecs[0]?.warehouse || 'San Francisco'
        const primaryCategory = selectedRecs[0]?.category || 'Circuit Boards'

        // Submit order
        await api.createOrder({
          customer: 'Internal Restocking',
          items: items,
          total_value: selectedSummary.value.totalCost,
          order_type: 'restocking',
          expected_delivery: deliveryDate.toISOString(),
          warehouse: primaryWarehouse,
          category: primaryCategory
        })

        // Redirect to orders
        router.push('/orders')
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
        console.error('Submit error:', err)
      } finally {
        submitting.value = false
      }
    }

    const getTrendClass = (trend) => {
      const trendMap = {
        'increasing': 'success',
        'stable': 'info',
        'decreasing': 'warning'
      }
      return trendMap[trend] || 'info'
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    onMounted(() => {
      loadData()
    })

    return {
      t,
      loading,
      error,
      budgetAmount,
      maxBudget,
      displayedRecommendations,
      selectedItems,
      selectedSummary,
      canSubmit,
      submitting,
      formatCurrency,
      toggleItem,
      submitRestockingOrder,
      getTrendClass,
      translateProductName
    }
  }
}
</script>

<style scoped>
/* Fixed table layout */
.recommendations-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-checkbox {
  width: 50px;
  text-align: center;
}

.col-sku {
  width: 120px;
}

.col-name {
  width: 200px;
}

.col-category {
  width: 150px;
}

.col-stock {
  width: 120px;
}

.col-trend {
  width: 120px;
}

.col-qty {
  width: 100px;
}

.col-unit-cost {
  width: 100px;
}

.col-total {
  width: 120px;
}

.checkbox-input {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #2563eb;
}

.stock-info {
  display: flex;
  flex-direction: column;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.submit-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  margin-top: 1.5rem;
}

.summary {
  display: flex;
  gap: 2rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.submit-button {
  padding: 0.875rem 2rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-button:hover:not(:disabled) {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.submit-button:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
