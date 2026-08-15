<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Slider -->
    <div class="card budget-card">
      <div class="budget-header">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budget') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <div class="slider-wrapper">
        <span class="slider-min">{{ currencySymbol }}1,000</span>
        <input
          id="budget-slider"
          type="range"
          class="budget-slider"
          :min="1000"
          :max="50000"
          :step="500"
          v-model.number="budget"
        />
        <span class="slider-max">{{ currencySymbol }}50,000</span>
      </div>
      <div class="budget-ticks">
        <span>{{ currencySymbol }}1K</span>
        <span>{{ currencySymbol }}10K</span>
        <span>{{ currencySymbol }}20K</span>
        <span>{{ currencySymbol }}30K</span>
        <span>{{ currencySymbol }}40K</span>
        <span>{{ currencySymbol }}50K</span>
      </div>
    </div>

    <!-- Recommendations -->
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Order success message -->
      <div v-if="orderSuccess" class="success-banner">
        {{ t('restocking.orderSuccess') }} — {{ t('restocking.orderNumber') }}: <strong>{{ lastOrderNumber }}</strong>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <div class="budget-summary">
            <span class="summary-item">
              {{ t('restocking.selectedItems') }}: <strong>{{ selectedCount }}</strong>
            </span>
            <span class="summary-divider">|</span>
            <span class="summary-item">
              {{ t('restocking.totalCost') }}: <strong>{{ currencySymbol }}{{ selectedTotalCost.toLocaleString() }}</strong>
            </span>
            <span class="summary-divider">|</span>
            <span class="summary-item" :class="{ 'over-budget': remainingBudget < 0 }">
              {{ t('restocking.remainingBudget') }}: <strong>{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</strong>
            </span>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th class="col-check">{{ t('restocking.table.select') }}</th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="col-num">{{ t('restocking.table.currentStock') }}</th>
                <th class="col-num">{{ t('restocking.table.restockQty') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-cost">{{ t('restocking.table.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.sku"
                :class="{ 'row-selected': selectedSkus.has(item.sku), 'row-disabled': !selectedSkus.has(item.sku) && !canAfford(item) }"
              >
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(item.sku)"
                    @change="toggleItem(item)"
                    class="row-checkbox"
                  />
                </td>
                <td class="col-sku"><strong>{{ item.sku }}</strong></td>
                <td class="col-name">{{ item.name }}</td>
                <td class="col-trend">
                  <span :class="['badge', item.trend]">{{ t('trends.' + item.trend) }}</span>
                </td>
                <td class="col-num">{{ item.forecasted_demand }}</td>
                <td class="col-num">{{ item.current_stock }}</td>
                <td class="col-num"><strong>{{ item.restock_qty }}</strong></td>
                <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td class="col-cost"><strong>{{ currencySymbol }}{{ itemTotalCost(item).toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer">
          <button
            class="btn-primary"
            :disabled="selectedCount === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>

      <!-- Submitted Orders -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.submittedOrders') }}</h3>
        </div>

        <div v-if="submittedOrdersLoading" class="loading">{{ t('common.loading') }}</div>
        <div v-else-if="submittedOrders.length === 0" class="empty-state">
          {{ t('restocking.noSubmittedOrders') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.orderNumber') }}</th>
                <th>{{ t('restocking.items') }}</th>
                <th>{{ t('restocking.status') }}</th>
                <th>{{ t('restocking.orderDate') }}</th>
                <th>{{ t('restocking.expectedDelivery') }}</th>
                <th>{{ t('restocking.leadTime') }}</th>
                <th>{{ t('restocking.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td><strong>{{ order.order_number }}</strong></td>
                <td>{{ order.items_count }}</td>
                <td>
                  <span :class="['badge', getStatusClass(order.status)]">
                    {{ t('status.processing') }}
                  </span>
                </td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td>{{ leadTimeDays(order.order_date, order.expected_delivery) }} {{ t('restocking.days') }}</td>
                <td><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
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
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const budget = ref(10000)
    const recommendations = ref([])
    const submittedOrders = ref([])

    const loading = ref(false)
    const error = ref(null)
    const submittedOrdersLoading = ref(false)
    const submitting = ref(false)

    const orderSuccess = ref(false)
    const lastOrderNumber = ref('')

    // Set of SKUs that are currently selected
    const selectedSkus = ref(new Set())

    // Run greedy auto-select: pick items in priority order until budget exhausted
    const autoSelect = () => {
      const selected = new Set()
      let spent = 0

      for (const item of recommendations.value) {
        const cost = itemTotalCost(item)
        if (spent + cost <= budget.value) {
          selected.add(item.sku)
          spent += cost
        }
      }

      selectedSkus.value = selected
    }

    const itemTotalCost = (item) => {
      return item.unit_cost * item.restock_qty
    }

    const selectedCount = computed(() => selectedSkus.value.size)

    const selectedTotalCost = computed(() => {
      return recommendations.value
        .filter(item => selectedSkus.value.has(item.sku))
        .reduce((sum, item) => sum + itemTotalCost(item), 0)
    })

    const remainingBudget = computed(() => budget.value - selectedTotalCost.value)

    // Whether a non-selected item can be added within remaining budget
    const canAfford = (item) => {
      if (selectedSkus.value.has(item.sku)) return true
      return itemTotalCost(item) <= remainingBudget.value
    }

    const toggleItem = (item) => {
      // Create a new Set so Vue detects the change
      const next = new Set(selectedSkus.value)
      if (next.has(item.sku)) {
        next.delete(item.sku)
      } else {
        next.add(item.sku)
      }
      selectedSkus.value = next
    }

    const getStatusClass = (status) => {
      const map = {
        'processing': 'warning',
        'Processing': 'warning',
        'delivered': 'success',
        'Delivered': 'success',
        'shipped': 'info',
        'Shipped': 'info',
        'cancelled': 'danger',
        'Cancelled': 'danger'
      }
      return map[status] || 'warning'
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const leadTimeDays = (orderDate, deliveryDate) => {
      const d1 = new Date(orderDate)
      const d2 = new Date(deliveryDate)
      if (isNaN(d1.getTime()) || isNaN(d2.getTime())) return '—'
      return Math.round((d2 - d1) / (1000 * 60 * 60 * 24))
    }

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        recommendations.value = await api.getRestockingRecommendations()
        autoSelect()
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const loadSubmittedOrders = async () => {
      submittedOrdersLoading.value = true
      try {
        submittedOrders.value = await api.getSubmittedRestockingOrders()
      } catch (err) {
        console.error('Failed to load submitted orders:', err)
      } finally {
        submittedOrdersLoading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedCount.value === 0) return
      submitting.value = true
      orderSuccess.value = false
      try {
        const items = recommendations.value
          .filter(item => selectedSkus.value.has(item.sku))
          .map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.restock_qty,
            unit_cost: item.unit_cost
          }))

        const result = await api.submitRestockingOrder({ items, budget: budget.value })
        lastOrderNumber.value = result.order_number || result.id || ''
        orderSuccess.value = true

        // Refresh both tables after placing order
        await Promise.all([loadRecommendations(), loadSubmittedOrders()])
      } catch (err) {
        error.value = 'Failed to place restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    // Re-run greedy auto-select whenever budget changes
    watch(budget, () => {
      autoSelect()
    })

    onMounted(() => {
      loadRecommendations()
      loadSubmittedOrders()
    })

    return {
      t,
      currencySymbol,
      budget,
      recommendations,
      submittedOrders,
      loading,
      error,
      submittedOrdersLoading,
      submitting,
      orderSuccess,
      lastOrderNumber,
      selectedSkus,
      selectedCount,
      selectedTotalCost,
      remainingBudget,
      canAfford,
      toggleItem,
      itemTotalCost,
      getStatusClass,
      formatDate,
      leadTimeDays,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* Budget card */
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.slider-min,
.slider-max {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
  flex-shrink: 0;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(
    to right,
    #2563eb 0%,
    #2563eb calc((var(--val, 10000) - 1000) / 49000 * 100%),
    #e2e8f0 calc((var(--val, 10000) - 1000) / 49000 * 100%),
    #e2e8f0 100%
  );
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
  cursor: pointer;
  transition: box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
  cursor: pointer;
}

.budget-ticks {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  padding: 0 0.25rem;
}

.budget-ticks span {
  font-size: 0.75rem;
  color: #94a3b8;
}

/* Budget summary row */
.budget-summary {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: #64748b;
}

.summary-item strong {
  color: #0f172a;
}

.summary-divider {
  color: #cbd5e1;
}

.summary-item.over-budget strong {
  color: #dc2626;
}

/* Table column widths */
.recommendations-table {
  table-layout: fixed;
  width: 100%;
}

.col-check {
  width: 48px;
  text-align: center;
}

.col-sku {
  width: 110px;
}

.col-name {
  /* flexible */
}

.col-trend {
  width: 110px;
}

.col-num {
  width: 130px;
  text-align: right;
}

.col-cost {
  width: 120px;
  text-align: right;
}

/* Row states */
.row-selected {
  background: #eff6ff;
}

.row-selected:hover {
  background: #dbeafe !important;
}

.row-disabled {
  opacity: 0.45;
}

.row-checkbox {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
}

/* Card footer with action button */
.card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  margin-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #94a3b8;
  font-size: 0.938rem;
}
</style>
