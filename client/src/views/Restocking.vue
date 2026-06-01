<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <span class="budget-display">{{ formatCurrency(budget, currentCurrency.value) }}</span>
        </div>
        <div class="slider-wrapper">
          <input
            type="range"
            class="budget-slider"
            min="0"
            :max="maxBudget"
            step="500"
            v-model.number="budget"
          />
          <div class="slider-labels">
            <span class="slider-label-min">{{ formatCurrency(0, currentCurrency.value) }}</span>
            <span class="slider-label-max">{{ formatCurrency(maxBudget, currentCurrency.value) }}</span>
          </div>
        </div>
      </div>

      <!-- Success Banner -->
      <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>

      <!-- Submit Error -->
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendedItems.length }})</h3>
        </div>
        <div class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-item-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-unit-cost">{{ t('restocking.table.estUnitCost') }}</th>
                <th class="col-line-total">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="recommendedItems.length === 0">
                <td colspan="6" class="empty-state">{{ t('restocking.noRecommendations') }}</td>
              </tr>
              <tr v-for="item in recommendedItems" :key="item.id">
                <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
                <td class="col-item-name">{{ translateProductName(item.item_name) }}</td>
                <td class="col-trend">
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="col-qty">{{ item.qty }}</td>
                <td class="col-unit-cost">{{ formatCurrency(item.unitCost, currentCurrency.value) }}</td>
                <td class="col-line-total">{{ formatCurrency(item.lineTotal, currentCurrency.value) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="summary-row">
          <span>{{ t('restocking.runningTotal') }}: <strong>{{ formatCurrency(runningTotal, currentCurrency.value) }}</strong></span>
          <span>{{ t('restocking.remaining') }}: <strong>{{ formatCurrency(remainingBudget, currentCurrency.value) }}</strong></span>
        </div>

        <div class="place-order-container">
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)
    const forecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(0)

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [f, inv] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = f
        inventoryItems.value = inv
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const inventoryCostMap = computed(() => {
      const map = {}
      for (const item of inventoryItems.value) {
        map[item.sku] = item.unit_cost
      }
      return map
    })

    const estimatedUnitCost = (sku) => {
      let hash = 0
      for (let i = 0; i < sku.length; i++) hash = (hash * 31 + sku.charCodeAt(i)) >>> 0
      return Math.round((10 + (hash % 25000) / 100) * 100) / 100
    }

    const lineItems = computed(() => {
      return forecasts.value
        .map(f => {
          const qty = Math.max(f.forecasted_demand - f.current_demand, 0)
          const unitCost = inventoryCostMap.value[f.item_sku] ?? estimatedUnitCost(f.item_sku)
          return { ...f, qty, unitCost, lineTotal: qty * unitCost }
        })
        .filter(item => item.qty > 0)
        .sort((a, b) => {
          const trendOrder = (t) => t === 'increasing' ? 0 : 1
          const ta = trendOrder(a.trend)
          const tb = trendOrder(b.trend)
          if (ta !== tb) return ta - tb
          return b.qty - a.qty
        })
    })

    const maxBudget = computed(() => {
      if (lineItems.value.length === 0) return 0
      const total = lineItems.value.reduce((sum, item) => sum + item.lineTotal, 0)
      return Math.ceil(total / 1000) * 1000
    })

    const recommendedItems = computed(() => {
      const included = []
      let running = 0
      for (const item of lineItems.value) {
        if (running + item.lineTotal <= budget.value) {
          included.push(item)
          running += item.lineTotal
        }
      }
      return included
    })

    const runningTotal = computed(() => {
      return recommendedItems.value.reduce((sum, item) => sum + item.lineTotal, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - runningTotal.value
    })

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      const payload = {
        budget: budget.value,
        items: recommendedItems.value.map(f => ({
          item_sku: f.item_sku,
          item_name: f.item_name,
          quantity: f.qty,
          unit_price: f.unitCost
        }))
      }
      try {
        const order = await api.placeRestockOrder(payload)
        successMessage.value = t('restocking.orderPlaced', { number: order.order_number })
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadData())

    return {
      t,
      currentCurrency,
      loading,
      error,
      submitting,
      submitError,
      successMessage,
      budget,
      maxBudget,
      recommendedItems,
      runningTotal,
      remainingBudget,
      formatCurrency,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-display {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-wrapper {
  padding: 0.5rem 0 0.25rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
  height: 6px;
  display: block;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
}

.slider-label-min,
.slider-label-max {
  font-size: 0.75rem;
  color: #64748b;
}

.success-banner {
  background: #d1fae5;
  color: #065f46;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
  font-weight: 500;
  font-size: 0.938rem;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem;
  font-style: italic;
}

.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-sku {
  width: 120px;
}

.col-item-name {
  width: auto;
}

.col-trend {
  width: 120px;
}

.col-qty {
  width: 130px;
}

.col-unit-cost {
  width: 140px;
}

.col-line-total {
  width: 130px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  padding: 0.875rem 0.75rem 0.5rem;
  border-top: 1px solid #e2e8f0;
  color: #0f172a;
  font-size: 0.938rem;
}

.place-order-container {
  display: flex;
  justify-content: flex-end;
  padding: 0.75rem 0 0.25rem;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover {
  background: #2563eb;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
