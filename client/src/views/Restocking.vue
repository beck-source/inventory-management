<template>
  <div class="restocking">
    <PageHeader :title="t('restocking.title')" :subtitle="t('restocking.description')" />

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error && !success" class="error">{{ error }}</div>

    <template v-else-if="success">
      <div class="card success-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.successTitle') }}</h3>
        </div>
        <div class="success-body">
          <p class="success-message">{{ t('restocking.successMessage', { orderNumber: success.orderNumber }) }}</p>
          <div class="success-actions">
            <router-link to="/orders" class="btn-primary">{{ t('restocking.viewInOrders') }}</router-link>
            <button class="btn-secondary" @click="placeAnother">{{ t('restocking.placeAnother') }}</button>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-section">
          <div class="budget-controls">
            <input
              type="range"
              class="budget-slider"
              min="10000"
              max="1000000"
              step="10000"
              v-model.number="budget"
            />
            <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <p class="help-text">{{ t('restocking.budgetHelp') }}</p>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <p class="card-subtitle">{{ t('restocking.recommendationsHelp') }}</p>
        </div>

        <div v-if="cart.length === 0" class="empty-state">{{ t('restocking.noEligibleItems') }}</div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-include">{{ t('restocking.table.include') }}</th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.name') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-num">{{ t('restocking.table.forecast') }}</th>
                <th class="col-num">{{ t('restocking.table.current') }}</th>
                <th class="col-num">{{ t('restocking.table.gap') }}</th>
                <th class="col-qty">{{ t('restocking.table.quantity') }}</th>
                <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-num">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in cart"
                :key="item.sku"
                :class="{ excluded: !item.included }"
              >
                <td class="col-include">
                  <input type="checkbox" v-model="item.included" />
                </td>
                <td class="col-sku"><code>{{ item.sku }}</code></td>
                <td class="col-name">{{ item.name }}</td>
                <td class="col-trend">
                  <span class="badge" :class="item.trend">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="col-num">{{ item.forecast }}</td>
                <td class="col-num">{{ item.current }}</td>
                <td class="col-num">{{ item.gap }}</td>
                <td class="col-qty">
                  <input
                    type="number"
                    class="qty-input"
                    min="0"
                    :max="item.gap"
                    v-model.number="item.qty"
                    :disabled="!item.included"
                  />
                </td>
                <td class="col-num">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td class="col-num">
                  <strong>{{ currencySymbol }}{{ (item.included ? item.qty * item.unit_cost : 0).toLocaleString() }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="cart-summary">
          <div class="cart-totals">
            <div class="cart-total-line">
              <span class="cart-total-label">{{ t('restocking.cartTotal') }}:</span>
              <span class="cart-total-value">{{ currencySymbol }}{{ cartTotal.toLocaleString() }}</span>
            </div>
            <div class="cart-total-line">
              <span class="cart-total-label">{{ t('restocking.budgetRemaining') }}:</span>
              <span class="cart-total-value" :class="budgetRemaining < 0 ? 'over-budget' : 'under-budget'">
                {{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}
              </span>
            </div>
          </div>

          <div v-if="cartTotal > budget" class="warning-banner">
            {{ t('restocking.overBudgetWarning') }}
          </div>

          <div class="place-order-row">
            <button
              class="btn-place-order"
              :disabled="isPlaceOrderDisabled"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import PageHeader from '../components/PageHeader.vue'

export default {
  name: 'Restocking',
  components: {
    PageHeader
  },
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const success = ref(null)

    const forecasts = ref([])
    const budget = ref(250000)
    const cart = ref([])

    // Greedy not knapsack-optimal — deliberate simplicity choice appropriate for a demo with ~9 items.
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          forecast: f.forecasted_demand,
          current: f.current_demand,
          gap: f.forecasted_demand - f.current_demand,
          unit_cost: f.unit_cost,
        }))
        .filter(c => c.gap > 0)

      candidates.sort((a, b) => {
        if (a.trend === 'increasing' && b.trend !== 'increasing') return -1
        if (a.trend !== 'increasing' && b.trend === 'increasing') return 1
        return b.gap - a.gap
      })

      let remaining = budget.value
      return candidates.map(c => {
        let qty = 0
        const fullCost = c.gap * c.unit_cost
        if (fullCost <= remaining) {
          qty = c.gap
          remaining -= fullCost
        } else {
          const partial = Math.floor(remaining / c.unit_cost)
          if (partial >= 1) {
            qty = partial
            remaining -= qty * c.unit_cost
          }
        }
        return { ...c, qty }
      })
    })

    watch(recommendations, (recs) => {
      cart.value = recs.map(r => ({ ...r, included: r.qty > 0 }))
    })

    const cartTotal = computed(() =>
      cart.value.reduce((sum, item) => sum + (item.included ? item.qty * item.unit_cost : 0), 0)
    )

    const budgetRemaining = computed(() => budget.value - cartTotal.value)

    const isPlaceOrderDisabled = computed(() =>
      submitting.value ||
      success.value !== null ||
      cartTotal.value > budget.value ||
      !cart.value.some(i => i.included && i.qty > 0)
    )

    const loadForecasts = async () => {
      loading.value = true
      error.value = null
      try {
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      error.value = null
      try {
        const items = cart.value
          .filter(i => i.included && i.qty > 0)
          .map(i => ({ sku: i.sku, name: i.name, quantity: i.qty, unit_price: i.unit_cost }))
        const response = await api.placeRestockingOrder({ items })
        success.value = { orderNumber: response.order_number }
      } catch (err) {
        error.value = 'Failed to place restocking order'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const placeAnother = async () => {
      success.value = null
      error.value = null
      await loadForecasts()
    }

    onMounted(loadForecasts)

    return {
      t,
      currencySymbol,
      loading,
      error,
      submitting,
      success,
      budget,
      cart,
      cartTotal,
      budgetRemaining,
      isPlaceOrderDisabled,
      placeOrder,
      placeAnother,
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

/* Budget slider */
.budget-section {
  padding: 1.25rem 1.5rem 1.5rem;
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider {
  flex: 1;
  max-width: 480px;
  accent-color: #2563eb;
  cursor: pointer;
  height: 6px;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 110px;
}

.help-text {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

/* Card subtitle */
.card-subtitle {
  font-size: 0.813rem;
  color: #64748b;
  margin: 0.25rem 1.5rem 0;
  padding-bottom: 1rem;
}

/* Table */
.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-include { width: 54px; text-align: center; }
.col-sku     { width: 120px; }
.col-name    { width: 200px; }
.col-trend   { width: 110px; }
.col-num     { width: 100px; text-align: right; }
.col-qty     { width: 90px; text-align: center; }

tbody tr.excluded {
  opacity: 0.45;
}

tbody tr.excluded td {
  text-decoration: line-through;
}

.qty-input {
  width: 68px;
  padding: 0.25rem 0.375rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #0f172a;
  text-align: center;
}

.qty-input:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

/* Cart summary */
.cart-summary {
  padding: 1.25rem 1.5rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.cart-totals {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.cart-total-line {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.cart-total-label {
  font-size: 0.938rem;
  color: #64748b;
  min-width: 160px;
}

.cart-total-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
}

.cart-total-value.under-budget {
  color: #16a34a;
}

.cart-total-value.over-budget {
  color: #dc2626;
}

/* Warning banner */
.warning-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

/* Buttons */
.place-order-row {
  display: flex;
  justify-content: flex-end;
}

.btn-place-order {
  background: #2563eb;
  color: white;
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-place-order:not(:disabled):hover {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty state */
.empty-state {
  padding: 2rem 1.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Success card */
.success-card .success-body {
  padding: 1.5rem;
}

.success-message {
  font-size: 1rem;
  color: #0f172a;
  margin-bottom: 1.5rem;
}

.success-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-primary {
  display: inline-block;
  background: #2563eb;
  color: white;
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: white;
  color: #0f172a;
  padding: 0.625rem 1.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: border-color 0.15s;
}

.btn-secondary:hover {
  border-color: #94a3b8;
}
</style>
