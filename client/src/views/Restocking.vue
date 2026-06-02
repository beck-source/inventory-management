<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          :step="sliderStep"
          v-model.number="budget"
        />
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendationsTitle') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.recommendedQty') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rec in recommendations" :key="rec.sku">
                  <td><strong>{{ rec.sku }}</strong></td>
                  <td>{{ translateProductName(rec.name) }}</td>
                  <td>{{ rec.quantity }}</td>
                  <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                  <td><strong>{{ currencySymbol }}{{ rec.lineTotal.toLocaleString() }}</strong></td>
                  <td>
                    <span :class="['badge', rec.trend]">
                      {{ t(`trends.${rec.trend}`) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="totals">
            <div class="total-row">
              <span class="total-label">{{ t('restocking.totalCost') }}</span>
              <span class="total-amount">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</span>
            </div>
            <div class="total-row">
              <span class="total-label">{{ t('restocking.remaining') }}</span>
              <span class="total-amount">{{ currencySymbol }}{{ remaining.toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || totalCost === 0 || submitting || !!placedOrderNumber"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>

        <div v-if="placedOrderNumber" class="order-success">
          {{ t('restocking.orderPlaced', { orderNumber: placedOrderNumber }) }}
          <router-link to="/orders" class="view-orders-link">
            {{ t('restocking.viewInOrders') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])

    // User-controlled restock budget (drives the recommendations below)
    const budget = ref(100000)

    const submitting = ref(false)
    const placedOrderNumber = ref(null)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        // Start the budget at the slider ceiling so every eligible item is funded
        // up front; the user drags down to trim. sliderMax derives from the data
        // just loaded, so reading it here reflects the fresh forecasts.
        budget.value = sliderMax.value
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Eligible restock candidates: rising-demand items that are actually short
    // on stock and have a positive unit cost (so the budget math can't divide by
    // zero). shortfall = extra units needed to cover forecasted demand. Sorted so
    // the budget covers the biggest shortfalls first.
    const eligibleItems = computed(() => {
      return forecasts.value
        .filter(f => f.trend === 'increasing' && f.unit_cost > 0)
        .map(f => ({
          ...f,
          shortfall: Math.max(f.forecasted_demand - f.current_demand, 0)
        }))
        .filter(f => f.shortfall > 0)
        .sort((a, b) => b.shortfall - a.shortfall)
    })

    // Budget needed to fully fund every eligible item.
    const maxEligibleCost = computed(() => {
      return eligibleItems.value.reduce((sum, i) => sum + i.shortfall * i.unit_cost, 0)
    })

    // Scale the slider to the data: cap it just above the cost of funding
    // everything (rounded up to a clean increment) so dragging the budget
    // meaningfully adds/removes items across the whole range instead of sitting
    // far past the point where all items are already funded.
    const sliderMax = computed(() => Math.max(1000, Math.ceil(maxEligibleCost.value / 500) * 500))
    const sliderStep = computed(() => Math.max(1, Math.round(sliderMax.value / 100)))

    // Greedy budget-constrained restock recommendations.
    // Recomputes automatically whenever the budget or forecasts change.
    const recommendations = computed(() => {
      const result = []
      let remainingBudget = budget.value

      for (const item of eligibleItems.value) {
        const fullCost = item.shortfall * item.unit_cost

        if (fullCost <= remainingBudget) {
          // Whole shortfall fits within the remaining budget: take it all.
          remainingBudget -= fullCost
          result.push({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.shortfall,
            unit_cost: item.unit_cost,
            lineTotal: fullCost,
            trend: item.trend
          })
        } else {
          // Not enough budget for the full shortfall: take as many whole units
          // as the leftover budget allows. This exhausts the budget, so stop.
          const affordableQty = Math.floor(remainingBudget / item.unit_cost)
          if (affordableQty >= 1) {
            const lineTotal = affordableQty * item.unit_cost
            remainingBudget -= lineTotal
            result.push({
              sku: item.item_sku,
              name: item.item_name,
              quantity: affordableQty,
              unit_cost: item.unit_cost,
              lineTotal,
              trend: item.trend
            })
          }
          // Budget can't fund even a single unit (or has just been exhausted) —
          // remaining lower-priority items are skipped.
          break
        }
      }

      return result
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + rec.lineTotal, 0)
    })

    const remaining = computed(() => {
      return budget.value - totalCost.value
    })

    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        placedOrderNumber.value = null

        const payload = {
          items: recommendations.value.map(rec => ({
            sku: rec.sku,
            name: rec.name,
            quantity: rec.quantity,
            unit_price: rec.unit_cost
          }))
        }

        const order = await api.createRestockOrder(payload)
        placedOrderNumber.value = order.order_number
      } catch (err) {
        error.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    // Clear the "order placed" state when the budget changes so the user can
    // submit a fresh order; this also prevents double-submitting the same set.
    watch(budget, () => {
      placedOrderNumber.value = null
    })

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      sliderMax,
      sliderStep,
      currencySymbol,
      recommendations,
      totalCost,
      remaining,
      submitting,
      placedOrderNumber,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.no-recommendations {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.totals {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 320px;
  margin-left: auto;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.total-amount {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-success {
  margin-top: 1rem;
  padding: 1rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #0f172a;
  font-size: 0.938rem;
}

.view-orders-link {
  margin-left: 0.5rem;
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
}

.view-orders-link:hover {
  color: #2563eb;
  text-decoration: underline;
}
</style>
