<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget slider -->
      <div class="card budget-card">
        <div class="budget-head">
          <div>
            <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
            <div class="budget-hint">{{ t('restocking.budgetHint') }}</div>
          </div>
          <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <input
          type="range"
          class="budget-slider"
          :min="0"
          :max="sliderMax"
          :step="500"
          v-model.number="budget"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(sliderMax, currentCurrency) }}</span>
        </div>
      </div>

      <!-- Success banner (after placing an order) -->
      <div v-if="placedOrder" class="success-banner">
        <span>{{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}</span>
        <router-link to="/orders" class="link-btn">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendedTitle') }} ({{ recommendation.items.length }})
          </h3>
          <button
            class="place-order-btn"
            :disabled="recommendation.items.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <!-- Empty states: no priced candidates at all, vs. budget too low -->
        <div v-if="candidates.length === 0" class="empty-state">{{ t('restocking.noMatches') }}</div>
        <div v-else-if="recommendation.items.length === 0" class="empty-state">{{ t('restocking.budgetTooLow') }}</div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.demand') }}</th>
                <th class="num">{{ t('restocking.table.restockQty') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['trend-badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.current_demand }} &rarr; {{ item.forecasted_demand }}</td>
                <td class="num">{{ item.restock_qty }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td class="num"><strong>{{ formatCurrencyWithDecimals(item.line_cost, currentCurrency, 2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary footer -->
        <div v-if="recommendation.items.length > 0" class="summary">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.summaryItems') }}</span>
            <span class="summary-num">{{ recommendation.items.length }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-num">{{ formatCurrencyWithDecimals(recommendation.totalCost, currentCurrency, 2) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.budgetRemaining') }}</span>
            <span class="summary-num">{{ formatCurrencyWithDecimals(budget - recommendation.totalCost, currentCurrency, 2) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Growth-first priority: increasing-demand items are restocked before stable/decreasing ones
const TREND_RANK = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(5000)          // USD base; display converts per locale
    const sliderMax = ref(100000)
    const candidates = ref([])        // forecast items priced from matching inventory
    const placing = ref(false)
    const placedOrder = ref(null)

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])

        // Index inventory by SKU so each forecast can pick up a real unit_cost
        const bySku = {}
        inventory.forEach(inv => { bySku[inv.sku] = inv })

        // Keep only forecast items that (a) match a priced inventory item and
        // (b) actually need restocking (forecast demand exceeds current demand)
        candidates.value = forecasts
          .filter(f => bySku[f.item_sku] && f.forecasted_demand > f.current_demand)
          .map(f => {
            const inv = bySku[f.item_sku]
            const restock_qty = f.forecasted_demand - f.current_demand
            return {
              sku: f.item_sku,
              name: f.item_name,
              trend: f.trend,
              current_demand: f.current_demand,
              forecasted_demand: f.forecasted_demand,
              gap: restock_qty,
              unit_cost: inv.unit_cost,
              restock_qty,
              line_cost: restock_qty * inv.unit_cost
            }
          })
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Growth-first, greedy fill: sort by trend priority then largest demand gap,
    // then add items one by one while the running total still fits the budget.
    const recommendation = computed(() => {
      const sorted = [...candidates.value].sort((a, b) => {
        const rank = TREND_RANK[a.trend] - TREND_RANK[b.trend]
        return rank !== 0 ? rank : b.gap - a.gap
      })

      const items = []
      let totalCost = 0
      for (const item of sorted) {
        if (totalCost + item.line_cost <= budget.value) {
          items.push(item)
          totalCost += item.line_cost
        }
      }
      return { items, totalCost }
    })

    const placeOrder = async () => {
      if (recommendation.value.items.length === 0) return
      try {
        placing.value = true
        error.value = null
        const payload = {
          items: recommendation.value.items.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.restock_qty,
            unit_price: r.unit_cost
          })),
          warehouse: null
        }
        placedOrder.value = await api.createOrder(payload)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      loading,
      error,
      budget,
      sliderMax,
      candidates,
      recommendation,
      placing,
      placedOrder,
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

.loading, .error {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.error {
  color: #ef4444;
}

/* Budget slider card */
.budget-card {
  padding: 1.5rem;
}

.budget-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-hint {
  font-size: 0.8125rem;
  color: #64748b;
  margin-top: 0.125rem;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2563eb;
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #fff;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
}

/* Success banner */
.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  border-radius: 10px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.link-btn {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

/* Place order button */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.place-order-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
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

.empty-state {
  padding: 2rem 1.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

/* Trend badges */
.trend-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.trend-badge.increasing { background: #d1fae5; color: #065f46; }
.trend-badge.stable { background: #dbeafe; color: #1e40af; }
.trend-badge.decreasing { background: #fee2e2; color: #991b1b; }

.restock-table {
  width: 100%;
}

.restock-table th.num,
.restock-table td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Summary footer */
.summary {
  display: flex;
  gap: 2.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
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
}

.summary-num {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
</style>
